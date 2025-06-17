import os
import json
import requests
from .http import HTTPClient
import pandas as pd
import logging

# logging
logger = logging.getLogger(__name__)


ROW_LIMIT = 10000


class ActionNetworkClient(HTTPClient):
    base_url = "https://actionnetwork.org/api/v2"

    def __init__(self, api_token: str = None, *args, **kwargs):
        self.api_token = api_token or os.environ.get("ACTIONNETWORK_API_TOKEN")
        super().__init__(*args, **kwargs)

    def create_session(self) -> requests.Session:
        """Creates ActionNetwork session"""
        headers = {"OSDI-API-Token": self.api_token, "Content-Type": "application/json"}
        session = requests.Session()
        session.headers.update(headers)
        return session

    def transform_response(self, response: requests.Response, **kwargs) -> dict:
        """Transforms ActionNetwork response into dict"""
        try:
            data = response.json() or {}
        except json.decoder.JSONDecodeError:
            data = {}
        data["status_code"] = response.status_code
        return data

    def check_response_for_rate_limit(
        self, response: requests.Response
    ) -> [int, float, None]:
        """Checks ActionNetwork response for rate limit, always returns 1"""
        return 1

    @staticmethod
    def extract_action_network_id(identifiers: list[str]) -> str:
        """
        Action Network may have a list of identifiers for a given person.
        This function grabs the Action Network ID.
        Refer to https://actionnetwork.org/docs/v2/ for more information

        :param identifiers: A list of Action Network identifier strings associated with a person.
        :return: The extracted Action Network ID, or an empty string if an Action Network ID is not found.
        """
        for identifier in identifiers:
            if identifier.startswith("action_network:"):
                return identifier.split(":", 1)[1]
        return ""

    def create_people_dataframe(self, people_data: list[dict]) -> pd.DataFrame:
        """
        Given an iterable of Action Network people from the Action Network people endpoint, returns a pandas dataframe
        with fields:
            * action_network_id
            * first_name
            * last_name
            * email_address
            * phone
            * zip5
            * street_name
            * city
            * state
        Refer to https://actionnetwork.org/docs/v2/people for more information

        :param people_data: A list of people dictionaries returned by the Action Network API, from the people endpoint
        :return: Pandas dataframe with person fields

        """
        rows = []
        for person in people_data:
            # common to all address fields
            address = person.get("postal_addresses", [{}])[0]
            rows.append(
                {
                    "action_network_id": self.extract_action_network_id(
                        person.get("identifiers", [""])
                    ),
                    "first_name": person.get("given_name", ""),
                    "last_name": person.get("family_name", ""),
                    "email_address": person.get("email_addresses", [{}])[0].get(
                        "address", ""
                    ),
                    "phone": person.get("phone_numbers", [{}])[0].get("number", ""),
                    "zip5": address.get("postal_code", "")[:5],
                    "street_name": address.get("address_lines", [""])[0],
                    "city": address.get("locality", ""),
                    "state": address.get("region", ""),
                }
            )
        return pd.DataFrame(rows)

    def paginate_endpoint(
        self, base_endpoint: str, embedded_key: str, max_pages: int = None, **kwargs
    ) -> list[dict]:
        """
        Generic pagination helper for Action Network endpoints that return the "_embedded" resource, which all endpoints
        that are collections of items (i.e. forms, events, submissions, etc.) do

        :param base_endpoint: the endpoint to paginate (i.e "forms" )
        :param embedded_key: the expected key inside the "_embedded" object
                             (i.e "osdi:submissions" for base_endpoint "forms/{form_id}/submissions"
                              or   "osdi:forms" for base_endpoint "forms")
        :param max_pages: optional parameter to limit the number of pages (can be used for testing)
        :return: list of embedded items from all pages
        """
        results = []
        page = 1

        while True:
            full_endpoint = f"{base_endpoint}?page={page}"
            data = self.get(full_endpoint, **kwargs)

            embedded = data.get("_embedded", {})
            items = embedded.get(embedded_key, [])
            if not items:
                # should flag end of pagination
                logger.debug(f"No items found at page {page} for key '{embedded_key}'")
                break

            results.extend(items)

            if max_pages is not None and page >= max_pages:
                break

            page += 1

        return results

    def fetch_related_people(
        self, resource: dict, person_link_keys: list[str] = None, **kwargs
    ) -> list[dict]:
        """
        Given a resource dict (i.e. a submission or signup), fetches all related person records
        from the Action Network API by following links in the `_links` section.

        Note this will only work for Action Network resources that have a person reference in the _links section

        When using this function, please add error handling in the caller function, for action_network_ids not found
            * requests.exceptions.HTTPError: 404 Client Error

        :param resource: the resource dict containing `_links`
        :param person_link_keys: optional list of keys in `_links` that indicate person links;
                                 defaults to ['osdi:person'] but can include others if relevant (i.e. osdi:creator)
        :return: list of person dicts fetched
        """
        # default to 'osdi:person'
        if person_link_keys is None:
            person_link_keys = ["osdi:person"]

        people = []
        links = resource.get("_links", {})

        # go through each relevant key in _link for the signups
        for key in person_link_keys:
            link_info = links.get(key)
            if not link_info:
                continue

            # assumes 1 href per _link key
            href = link_info.get("href")

            if not href or "people/" not in href:
                continue

            # Extract action network id from url
            action_network_id = href.split("people/")[-1]

            # this can lead to errors, so log them in the caller function ...
            person = self.get(f"people/{action_network_id}", **kwargs)
            people.append(person)

        return people
