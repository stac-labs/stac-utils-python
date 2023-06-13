import time
import logging
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Union

import requests

logger = logging.getLogger(__name__)


class Client(ABC):
    """
    Basic API client class
    """

    def __init__(self, *args, **kwargs):
        self._session = None
        self._session_count = 0

    @property
    def session(self):
        """
        Instead of passing session around, use the client's
        current context manager
        """
        if self._session is None:
            self._session = self.create_session()
        return self._session

    @abstractmethod
    def create_session(self):
        """
        Create a session, set headers & auth
        """

    @contextmanager
    def session_context(self):
        """
        Creates a context manager for a session
        """

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
    def call_api(self, *args, **kwargs):
        """
        Make an API request
        """

    @abstractmethod
    def transform_response(self, *args, **kwargs):
        """
        Transform the response from the API
        """

    @abstractmethod
    def check_for_error(self, *args, **kwargs):
        """
        Check a valid API response for error messages
        and raise an exception as needed
        """


class HTTPClient(Client):
    """
    HTTP Client class built on Client class
    """

    base_url = "ERROR"
    retry_limit = 3
    retry_wait = 7
    max_connections = 25

    def __init__(self, *args, **kwargs):
        self._rate_limits = None

        super().__init__(*args, **kwargs)

    @property
    def rate_limits(self) -> dict:
        """
        Get the rate limits for all the resources
        """
        if self._rate_limits is None:
            self._rate_limits = self.update_rate_limits()

        return self._rate_limits

    def wait_for_rate(self, endpoint: str, response: requests.Response):
        """
        Wait for the rate limit to pass

        :param endpoint: Specified API endpoint
        """

        rate_wait = self.check_response_for_rate_limit(response)

        if rate_wait is None:
            rate_limit = self.rate_limits.get(endpoint)

            if rate_limit:
                requests_made, window = rate_limit
                rate_wait = window * 60 / requests_made
            else:
                rate_wait = self.retry_wait

        time.sleep(rate_wait)

    def check_response_for_rate_limit(
        self, response: requests.Response
    ) -> Union[int, float, None]:
        """
        Inspect the response for rate limit information
        """

        return None

    def format_url(self, endpoint: str) -> str:
        """
        Prepare the URL for a request

        :param endpoint: Specified API endpoint
        :return: URL
        """

        url = f"{self.base_url.strip('/')}/{endpoint.strip('/')}"

        return url

    def call_api(
        self,
        method: str,
        endpoint: str,
        params: dict = None,
        body: dict = None,
        return_headers: bool = False,
        use_snake_case: bool = True,
        override_error_logging: bool = False,
        override_data_printing: bool = False,
        **kwargs,
    ):
        """
        Basic API request, retries on failures, parses errors

        :param method: Specified API method
        :param endpoint: Specified API endpoint
        :param params: Specified parameters for API call
        :param body: Specified body for API call
        :param return_headers: `False` by default, set `True` if returning headers is desired
        :param use_snake_case: `True` by default, set `False` if camel case or other is desired
        :param override_error_logging: `False` by default, set `True` if logging not desired
        :param override_data_printing: `False` by default, set `True` if data printing not desired
        :return: Data from API call
        """

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
                data = self.transform_response(
                    resp, return_headers=return_headers, use_snake_case=use_snake_case
                )

                self.check_for_error(resp, data, override_error_logging)

                if resp.status_code in [429]:
                    print("429: Rate limit")
                    fails += 1
                    self.wait_for_rate(endpoint, resp)
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

        if not override_data_printing:
            print(data)

        return data

    def get(self, *args, **kwargs):
        """
        Convenience wrapper for GET

        Example usage: `self.van.get(f"events/{event_id}?$expand=locations,roles,shifts")`
        """
        return self.call_api("GET", *args, **kwargs)

    def post(self, *args, **kwargs):
        """
        Convenience wrapper for POST.

        Example usage: `self.van.post("signups", body=payload)`
        """
        return self.call_api("POST", *args, **kwargs)

    def put(self, *args, **kwargs):
        """
        Convenience wrapper for PUT

        Example usage: `self.van.put(endpoint, params=params, body=payload)`
        """
        return self.call_api("PUT", *args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Convenience wrapper for DELETE
        """
        return self.call_api("DELETE", *args, **kwargs)

    def update(self, *args, **kwargs):
        """
        Convenience wrapper for UPDATE

        Example usage: self.match_dict.update(
                    {str(self.json_created["vanId"]): str(response["vanId"])}
                )
        """
        return self.call_api("UPDATE", *args, **kwargs)

    def patch(self, *args, **kwargs):
        """
        Convenience wrapper for PATCH
        """
        return self.call_api("PATCH", *args, **kwargs)

    def update_rate_limits(self) -> dict[str, tuple[int, int]]:
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

    def clean_up(self, response: requests.Response, data):
        """Clean up step to free memory that wouldn't normally be
        garbage collected (ie: soup.decompose() for BeautifulSoup)
        """

    def check_for_error(self, *args, **kwargs):
        """Check a valid API response for error messages
        and raise an exception as needed
        """

    def transform_response(self, response: requests.Response, **kwargs):
        """Transform the response from the API"""

        return response.content
