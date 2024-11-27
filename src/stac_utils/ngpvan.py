import json
import logging
import os
import requests

from .convert import convert_to_snake_case, strip_dict
from .http import HTTPClient

logger = logging.getLogger(__name__)


class NGPVANException(Exception):
    pass


class NGPVANLocationException(Exception):
    pass


class NGPVANClient(HTTPClient):
    """
    NGPVAN Client class built on basic HTTP Client class

    Parameters
    ==========
    mode: 0 for My Voters, 1 for everything else
    app_name: app name of the API key, will pick up "NGPVAN_APP_NAME" if it's in the environment
    api_key: the API key, will pick up "NGPVAN_API_KEY" if it's in the environment
    """

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
        """
        Creates and returns session
        """
        headers = {"content-type": "application/json"}
        session = requests.Session()
        session.headers.update(headers)
        session.auth = (self.app_name, self.api_key)

        return session

    def check_response_for_rate_limit(self, response: requests.Response) -> int:
        """
        Checks response for rate limits and returns
        """
        return 2

    def transform_response(
        self,
        response: requests.Response,
        return_headers: bool = False,
        use_snake_case: bool = True,
    ) -> dict:
        """
        Transforms response given specifications and returns data

        :param response: API response
        :param return_headers: `False` by default, set `True` if return headers desired
        :param use_snake_case: `True` by default, set `False` if camel case or something else desired
        :return: Data
        """
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
        """
        Checks for errors given specifications

        :param response: API response
        :param data: Data to check
        :param override_error_logging: `False` by default, set `True` if overriding logging desired
        """
        errors = data.get("errors")
        if errors:
            location_error_text = "'location' is required by the specified Event"
            if (
                len(errors) == 1
                and errors[0].get("text") == location_error_text
                and override_error_logging
            ):
                # This error means that the existing event needs a new location added
                # so we will do that first, without logging an error, and then retry the signup
                raise NGPVANLocationException(errors)

            # successful 204 response code does not raise error (i.e. when applying ACs/SQs)
            elif (
                response.status_code == 204
                and errors == "Expecting value: line 1 column 1 (char 0)"
            ):
                pass
            else:
                logger.error(response.content)
                raise NGPVANException(errors)

    def get_paginated_items(self, url, **kwargs):
        """
        Given a URL, gets paginated items. For example with NGP, most likely to be used for pulling saved lists.

        :param url: Given URL where paginated items exist
        :return: All items as list
        """
        all_items = []
        next_url = url
        while next_url:
            print(f"Getting {next_url}")
            data = self.get(next_url, **kwargs)
            if "items" not in data or len(data.get("items")) == 0:
                return all_items
            all_items.extend(data["items"])

            next_full_url = data.get("next_page_link")
            next_url = next_full_url.split("/")[-1] if next_full_url else None
        return all_items

    @staticmethod
    def format_person_json(row: dict, id_key: str, has_identifier: bool) -> dict:
        formatted_json = {
            "firstName": row.get("first_name"),
            "lastName": row.get("last_name"),
            "dateOfBirth": row.get("date_of_birth"),
            "contactMode": "Person",
        }

        if has_identifier and id_key is not None:
            formatted_json["identifiers"] = [
                {"type": "votervanid", "externalId": row.get(id_key)}
            ]
        elif has_identifier and id_key is None:
            raise ValueError("did not indicate name of id key column")
        elif row.get("custom_field_id") and row.get("custom_field_group_id"):
            formatted_json["customFieldValues"] = [
                {
                    "custom_field_id": row.get("custom_field_id"),
                    "custom_field_group_id": row.get("custom_field_group_id"),
                    "assignedValue": row.get(id_key),
                }
            ]
        else:
            print("No ID key used")

        if row.get("email"):
            formatted_json["emails"] = [{"email": row.get("email").strip()}]

        if row.get("phone"):
            formatted_json["phones"] = [
                {"phoneNumber": str(row.get("phone")).replace(".0", "")}
            ]

        if row.get("middle_name"):
            formatted_json["middleName"] = row.get("middle_name")

        address = {}

        if row.get("street_address"):
            address["addressLine1"] = row.get("street_address")

        if row.get("city"):
            address["city"] = row.get("city")

        if row.get("state") or row.get("stateOrProvince"):
            if row.get("state"):
                address["stateOrProvince"] = row.get("state")
            else:
                address["stateOrProvince"] = row.get("stateOrProvince")

        if row.get("zip") or row.get("zipOrPostalCode"):
            if row.get("zip"):
                address["zipOrPostalCode"] = row.get("zip")
            else:
                address["zipOrPostalCode"] = row.get("zipOrPostalCode")

        if address:
            formatted_json["addresses"] = [address]

        return strip_dict(formatted_json)

    def validate_phone(self, phone: str) -> str:
        """
        This method validates phone numbers using VAN's API, and if number is not valid the phone variable
        is assigned an empty string
        :param phone: str, phone number from ActionKit
        :return: str, empty string if phone number was not valid, or returns the valid phone number
        """
        van_phone_endpoint = "people/findByPhone"
        payload = {"phoneNumber": f"{phone}"}
        try:
            response = self.post(van_phone_endpoint, body=payload)
            phone = response["findbyphone"]
        except NGPVANException:
            phone = ""

        return phone
