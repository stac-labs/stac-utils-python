import json
import logging
import os

import requests

from .convert import convert_to_snake_case
from .http import HTTPClient

logger = logging.getLogger(__name__)


class NGPVANException(Exception):
    pass


class NGPVANLocationException(Exception):
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
        self,
        response: requests.Response,
        return_headers: bool = False,
        use_snake_case: bool = True,
    ) -> dict:
        try:
            data = response.json() or {}

            if type(data) is not dict:
                data = {str(response.url).split("/")[-1].lower(): data}

            if use_snake_case:
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

    def check_for_error(
        self,
        response: requests.Response,
        data: dict,
        override_error_logging: bool = False,
    ):
        errors = data.get("errors")
        if errors:
            LOCATION_ERROR_TEXT = "'location' is required by the specified Event"
            if (
                len(errors) == 1
                and errors[0].get("text") == LOCATION_ERROR_TEXT
                and override_error_logging
            ):
                ## This error means that the existing event needs a new location added
                ## so we will do that first, without logging an error, and then retry the signup
                raise NGPVANLocationException(errors)
            else:
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
