import json
import os
import time
import logging


from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Union, Tuple, Dict
import requests

from convert import convert_to_snake_case

logger = logging.getLogger(__name__)


class Client(ABC):
    def __init__(self, *args, **kwargs):
        self._session = None
        self._session_count = 0

    @property
    def session(self):
        """Instead of passing session around, use the client's
        current context manager
        """
        if self._session is None:
            self._session = self.create_session()
        return self._session

    @abstractmethod
    def create_session(self):
        """Create a session, set headers & auth"""

    @contextmanager
    def session_context(self):
        """Creates a context manager for a session"""

        self._session_count += 1
        try:
            yield self.session
        except ValueError:
            self._session = self.create_session()
            yield self.session
        finally:
            self._session_count -= 1
            if self._session_count == 0:
                self._session.close()
                self._session = None

    @abstractmethod
    def call_api(self, *args, **kwargs) -> Any:
        """Make an API request"""

    @abstractmethod
    def transform_response(self, *args, **kwargs) -> Any:
        """Transform the response from the API"""

    @abstractmethod
    def check_for_error(self, *args, **kwargs):
        """Check a valid API response for error messages
        and raise an exception as needed
        """


class HTTPClient(Client):
    base_url = "ERROR"
    retry_limit = 3
    retry_wait = 7
    max_connections = 25

    def __init__(self, *args, **kwargs):
        self._rate_limits = None

        super().__init__(*args, **kwargs)

    @property
    def rate_limits(self) -> dict:
        """Get the rate limits for all the resources"""
        if self._rate_limits is None:
            self._rate_limits = self.update_rate_limits()

        return self._rate_limits

    def wait_for_rate(self, endpoint: str, response: requests.Response):
        """Wait for the rate limit to pass"""

        rate_wait = self.check_response_for_rate_limit(response)

        if rate_wait is None:
            requests_made, window = self.rate_limits.get(endpoint)

            if requests_made and window:
                rate_wait = window * 60 / requests_made
            else:
                rate_wait = self.retry_wait

        time.sleep(rate_wait)

    def check_response_for_rate_limit(
        self, response: requests.Response
    ) -> Union[int, float, None]:
        """Inspect the response for rate limit information"""

        return None

    def format_url(self, endpoint: str) -> str:
        """Prepare the URL for a request"""

        url = f"{self.base_url.strip('/')}/{endpoint.strip('/')}"

        return url

    def call_api(
        self,
        method: str,
        endpoint: str,
        params: dict = None,
        body: dict = None,
        return_headers: bool = False,
        **kwargs,
    ) -> Any:
        """Basic API request, retries on failures, parses errors"""

        fails = 0
        print(f"{method} {endpoint}: {params} {body}")

        while True:
            time.sleep(fails * self.retry_wait)

            url = self.format_url(endpoint)
            resp = None

            try:
                resp = self.session.request(
                    method, url, params=params, json=body, **kwargs
                )
                data = self.transform_response(resp, return_headers=return_headers)

                self.check_for_error(resp, data)

                if resp.status_code in [429]:
                    print("429: Rate limit")
                    self.wait_for_rate(endpoint, resp)
                    fails += 1
                    continue
                elif resp.status_code in [401]:
                    print("401: Refreshing client auth")
                    fails += 1
                    self.refresh_auth(resp)

                resp.raise_for_status()
                self.check_for_error(resp, data)

                break

            except requests.exceptions.RequestException:
                fails += 1

                # 404s are not worth retrying
                try:
                    if resp.status_code in [404]:
                        raise
                except AttributeError:
                    # connection errors won't have a status code sometimes
                    pass

                if fails > self.retry_limit:
                    raise

        print(data)
        return data

    def get(self, *args, **kwargs):
        return self.call_api("GET", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.call_api("POST", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.call_api("DELETE", *args, **kwargs)

    def update(self, *args, **kwargs):
        return self.call_api("UPDATE", *args, **kwargs)

    def update_rate_limits(self) -> Dict[str, Tuple[int, int]]:
        """Update the rate limits for the API
        This could be a static function or calling the API

        Rate limits are a tuple of the number of requests allowed
        over a number of seconds.
        """

        return {}

    def create_session(self) -> requests.Session:
        """Create a session, set headers & auth"""

        session = requests.Session()
        return session

    def refresh_auth(self, response: requests.Response):
        """Makes a blocking auth request to the API"""

    def clean_up(self, response: requests.Response, data: Any):
        """Clean up step to free memory that wouldn't normally be
        garbage collected (ie: soup.decompose() for BeautifulSoup)
        """


class NGPVANException(Exception):
    pass


class NGPVANClient(HTTPClient):
    base_url = "https://api.securevan.com/v4"
    max_connections = 5

    def __init__(
        self, mode: int, app_name: str = None, api_key: str = None, *args, **kwargs
    ):
        self.app_name = app_name or os.environ.get("NGPVAN_APP_NAME")
        assert int(mode) in (0, 1)
        api_key = api_key or os.environ.get("NGPVAN_API_KEY")
        self.api_key = f"{api_key}|{mode}"

        super().__init__(*args, **kwargs)

    def create_session(self) -> requests.Session:
        headers = {"content-type": "application/json"}
        session = requests.Session()
        session.headers.update(headers)
        session.auth = (self.app_name, self.api_key)

        return session

    def check_response_for_rate_limit(self, response: requests.Response) -> int:
        return 2

    def transform_response(
        self, response: requests.Response, return_headers: bool = False
    ) -> dict:
        try:
            data = response.json() or {}

            if type(data) is not dict:
                data = {str(response.url).split("/")[-1].lower(): data}

            data = convert_to_snake_case(data)

        except requests.RequestException:
            data = {}

        except json.decoder.JSONDecodeError:
            data = {}

        except Exception as E:
            data = {"errors": str(E)}

        data["http_status_code"] = response.status_code

        if return_headers:
            data["headers"] = response.headers.copy()

        return data

    def check_for_error(self, response: requests.Response, data: dict):
        errors = data.get("errors")
        if errors:
            logger.error(response.content)
            raise NGPVANException(errors)

    def get_paginated_items(self, url, **kwargs):
        all_items = []
        next_url = url
        while next_url:
            print(f"Getting {url}")
            data = self.get(url, **kwargs)
            if "items" not in data:
                return all_items
            all_items.extend(data["items"])

            next_url = data.get("nextPageLink")
        return all_items
