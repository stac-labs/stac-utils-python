import os
import json
import requests
from .http import HTTPClient
import logging
import hashlib
from datetime import datetime, date
from typing import Any

# logging
logger = logging.getLogger(__name__)


class MailChimpClient(HTTPClient):
    """
    Mailchimp Utils for working with the Mailchimp API
    """

    def __init__(self, api_key: str = None, *args, **kwargs):
        self.api_key = api_key or os.environ.get("MAILCHIMP_API_KEY")

        # derive data center (i.e. 'us9') from API key suffix to get the base_url (no universal base_url here...)
        # see: https://mailchimp.com/developer/marketing/docs/fundamentals/#api-structure
        self.data_center = self.api_key.split("-")[-1]
        self.base_url = f"https://{self.data_center}.api.mailchimp.com/3.0"
        super().__init__(*args, **kwargs)

    def create_session(self) -> requests.Session:
        """Creates Mailchimp session"""
        session = requests.Session()
        #  https://mailchimp.com/developer/marketing/docs/fundamentals/#api-structure
        session.auth = ("anystring", self.api_key)
        session.headers.update({"Content-Type": "application/json"})
        return session

    def transform_response(self, response: requests.Response, **kwargs) -> dict:
        """
        Transforms MailChimp response into dict

        :param response: The HTTP response object returned by requests
        :return: response data as dict, always including a "status_code" key
        """
        try:
            # for handling 204 and empty responses
            if response.status_code != 204 and response.content:
                data = response.json() or {}
            else:
                data = {}
        except (ValueError, json.decoder.JSONDecodeError):
            data = {}
        data["status_code"] = response.status_code
        return data

    def check_response_for_rate_limit(self, response: requests.Response) -> int:
        """
        Checks Mailchimp response for rate limit, always returns 1

        :param response: the HTTP response object returned by requests
        :return: always returns 1
        """
        # added basic logging in this method...
        if response.status_code == 429:
            logger.warning("Mailchimp rate limit hit (HTTP 429: Too Many Requests)")
        return 1

    def paginate_endpoint(
        self,
        base_endpoint: str,
        data_key: str,
        count: int = 1000,
        max_pages: int = None,
        **kwargs,
    ) -> list[dict]:
        """
        Generic pagination helper for Mailchimp endpoints that return
        collections (i.e., lists, members, campaigns, etc.).

        :param base_endpoint: the endpoint to paginate (i.e "lists" or "lists/{list_id}/members").
        :param data_key: the expected key in the response dict (i.e "lists", "members").
        :param count: number of items to fetch per page (default set to 1000, which is MailChimp's max).
        :param max_pages: optional parameter to limit the number of pages (can be used for testing)
        :return:  a list of all collected items from the paginated responses
        """
        results = []
        page = 1

        # MailChimp uses offset to skip records for pagination
        # see: https://mailchimp.com/developer/marketing/docs/methods-parameters/#pagination
        offset = 0

        while True:
            params = {"count": count, "offset": offset, **kwargs}
            url = f"{self.base_url}/{base_endpoint}"
            response = self.session.get(url, params=params)
            data = self.transform_response(response)

            items = data.get(data_key, [])
            if not items:
                logger.debug(f"No items found at offset {offset} for key '{data_key}'")
                break

            results.extend(items)

            total = data.get("total_items", 0)

            # stop if max_pages is set and the page is max_pages
            if max_pages is not None and page >= max_pages:
                break

            # increment pagination and offset
            offset += count
            page += 1

            # if everything is fetched, stop!
            if offset >= total:
                break

        return results

    @staticmethod
    def get_subscriber_hash(email: str) -> str:
        """
        Return the Mailchimp subscriber hash for a given email.
        This is the unique identifier of the member, scoped to a given audience_id (list_id)

        :param email: the email to get the subscriber hash (MailChimp member id) for
        :return: subscriber hash  (MailChimp member id)
        """
        # see: https://mailchimp.com/developer/marketing/docs/methods-parameters/
        # borrowed from: https://endgrate.com/blog/using-the-mailchimp-api-to-create-members-%28with-python-examples%29
        return hashlib.md5(email.lower().encode()).hexdigest()

    def update_member_tags(
        self,
        list_id: str,
        email_address: str,
        tags: list[str],
        active: bool,
    ) -> dict:
        """
        This method adds or removes tags for a member.

        See: https://mailchimp.com/developer/marketing/api/list-member-tags/add-or-remove-member-tags/

        :param list_id: MailChimp audience (list) id
        :param email_address: member email address.
        :param tags: list of exact names of tags to add or remove.
        :param active: flags whether to add or remove the tags. True adds the tags, and False removes the tags.
        """
        # clean & dedupe tags + skip blanks
        cleaned = [
            tag.strip() for tag in (tags or []) if isinstance(tag, str) and tag.strip()
        ]

        # return for empty tag list (MailChimp returns 204 even with an empty tag payload, so this mimics that)
        if not cleaned:
            logger.info(f"No valid tags provided for email: {email_address}")
            return {"status_code": 204, "info": "No valid tags provided"}

        subscriber_hash = self.get_subscriber_hash(email_address)
        url = f"{self.base_url}/lists/{list_id}/members/{subscriber_hash}/tags"

        payload = {
            "tags": [
                {"name": tag, "status": "active" if active else "inactive"}
                for tag in cleaned
            ]
        }
        response = self.session.post(url, json=payload)
        return self.transform_response(response)

    def upsert_member(
        self,
        list_id: str,
        email_address: str,
        status_if_new: str = "subscribed",
        merge_fields: dict = None,
        **kwargs,
    ) -> dict:
        """
        Add or update a MailChimp member (contact) in a given audience (list_id).
        This method creates the member if they don't exist, using the status_if_new parameter
        If the member already exists, it will update only fields that are provided in merge_fields

        The merge_fields dict takes key:value pairs that update other fields (first name, last name, etc) for a given audience
        Because these fields are unique to a given audience id, you will have to find these in the "Audience fields
        and merge tags" section in MailChimp, and the keys will be the "Merge tag" without the *||*
        (i.e. (potentially) FNAME, LNAME, ADDRESS, etc). Tags must exist for the given audience or the
        request will error (HTTP 400)

        NOTE: by default, any merge fields that have "required" set to true in MailChimp MUST be included
        when adding a contact.

        Additional parameters you would like to add to the payload to pass to MailChimp API using **kwargs can be found here:
        https://mailchimp.com/developer/marketing/api/list-members/add-or-update-list-member/

        :param list_id: MailChimp audience (list) id
        :param email_address: member email address.
        :param merge_fields: PII fields unique to a MailChimp audience. Make sure to check the front end of MailChimp to get these fields
        :param status_if_new: subscriber's status that is used only when creating a new record. Valid values include "subscribed", "unsubscribed", "cleaned", "pending", or "transactional". Defaults to "subscribed".
        :return: dict value from the transform_response() method
        """

        subscriber_hash = self.get_subscriber_hash(email_address)
        url = f"{self.base_url}/lists/{list_id}/members/{subscriber_hash}"

        payload: dict = {
            "email_address": email_address,
            "status_if_new": status_if_new,
        }
        if merge_fields:
            # format merge fields
            formatted = self.format_merge_fields_for_list(list_id, merge_fields)
            # add non-empty merge_fields to payload
            if formatted:
                payload["merge_fields"] = formatted

        # in case you want to add other parameters to the payload, not covered in the existing parameters
        # see: https://mailchimp.com/developer/marketing/api/list-members/add-or-update-list-member/
        other_params = {
            key: value
            for key, value in kwargs.items()
            if value is not None
            and key not in {"email_address", "status_if_new", "merge_fields"}
        }
        payload.update(other_params)

        response = self.session.put(url, json=payload)
        return self.transform_response(response)

    def get_merge_fields_data_type_map(self, list_id: str, **kwargs) -> dict[str, str]:
        """
        This method provides a mapping of the merge field tags and data types for a given audience (list_id).
        i.e. {'BIRTHDAY': 'birthday', 'FNAME': 'text', 'LNAME': 'text'}

        see: https://mailchimp.com/developer/marketing/api/list-merges/list-merge-fields/

        :param list_id: MailChimp audience (list) id
        :return: dict mapping {"Merge Tag": "Data Type"}
        """
        fields = self.paginate_endpoint(
            base_endpoint=f"lists/{list_id}/merge-fields",
            data_key="merge_fields",
            **kwargs,
        )
        return {field["tag"]: field.get("type") for field in fields if field.get("tag")}

    def format_merge_fields_for_list(
        self,
        list_id: str,
        merge_fields: dict[str, Any],
    ) -> dict[str, Any]:
        """
        This method formats MailChimp merge fields for a given audience (list_id).

        see: https://mailchimp.com/developer/marketing/docs/merge-fields/#add-merge-data-to-contacts

        :param list_id: MailChimp audience (list) id
        :param merge_fields: MailChimp merge fields dict
        :return: formatted MailChimp merge fields dict
        """
        merge_fields_data_type_map = self.get_merge_fields_data_type_map(list_id)
        merge_fields_cleaned = {}

        for tag, value in (merge_fields or {}).items():
            # ignore blanks and empty string
            if value is None:
                continue
            if isinstance(value, str):
                value = value.strip()
                if value == "":
                    continue

            data_type = merge_fields_data_type_map.get(tag)

            # raise error if unknown tags (all tags should be valid)
            if data_type is None:
                raise KeyError(f"Unknown merge tag for this audience: {list_id}: {tag}")

            if data_type == "date":
                merge_fields_cleaned[tag] = self.format_date(value)
            elif data_type == "birthday":
                merge_fields_cleaned[tag] = self.format_birthday(value)
            elif data_type == "address":
                merge_fields_cleaned[tag] = self.format_address(value)
            elif data_type == "number":
                merge_fields_cleaned[tag] = self.format_number(value)
            elif data_type == "zip":
                if len(str(value)) > 5:
                    raise ValueError("Zip codes must be 5 digits")
                merge_fields_cleaned[tag] = str(value)
            else:
                # text, radio, dropdown, phone, url, imageurl -- all string
                merge_fields_cleaned[tag] = (
                    str(value)
                    if not isinstance(value, (int, float, bool, dict, list, tuple))
                    else value
                )

        return merge_fields_cleaned

    @staticmethod
    def format_date(val: Any) -> str:
        """
        Helper method to normalize date to YYYY-MM-DD

        see: https://mailchimp.com/developer/marketing/docs/merge-fields/#add-merge-data-to-contacts

        :param val: date value to normalize
        :return: normalized date in YYYY-MM-DD
        """
        # if in date/datetime
        if isinstance(val, (datetime, date)):
            return datetime(val.year, val.month, val.day).strftime("%Y-%m-%d")
        # if in string
        if isinstance(val, str):
            val = val.strip()
            # covers most common cases
            for format in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y"):
                try:
                    return datetime.strptime(val, format).strftime("%Y-%m-%d")
                except ValueError:
                    pass
        raise ValueError(f"Unable to parse the date value: {val}")

    @staticmethod
    def format_birthday(val: Any) -> str:
        """
        Helper method to normalize to MM/DD, which is the MailChimp birthday format

        see: https://mailchimp.com/developer/marketing/docs/merge-fields/#add-merge-data-to-contacts

        :param val: date value to normalize
        :return: normalized date in MM/DD
        """
        # if in date/datetime
        if isinstance(val, (datetime, date)):
            return f"{val.month:02d}/{val.day:02d}"
        # covers most common cases
        if isinstance(val, str):
            val = val.strip()
            # covers most cases
            for format in (
                "%m/%d",
                "%m-%d",
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%m/%d/%Y",
                "%d-%m-%Y",
                "%m-%d-%Y",
            ):
                try:
                    bday = datetime.strptime(val, format)
                    return f"{bday.month:02d}/{bday.day:02d}"
                except ValueError:
                    pass
        raise ValueError(f"Unable to parse the birthdate value: {val}")

    @staticmethod
    def format_address(val: Any) -> dict:
        """
        Helper method to ensure MailChimp address format is met
        Required fields are: addr1, city, state, zip
        Optional fields are: addr2, country

        see: https://mailchimp.com/developer/marketing/docs/merge-fields/#add-merge-data-to-contacts

        :param val: address dict value
        :return:  address dict value formatted
        """
        # if the input value is not a dict, then error
        if not isinstance(val, dict):
            raise ValueError("Address value must be a dict")

        def normalize_string(s: Any) -> str:
            """
            normalize the string
            """
            if s is None:
                return ""
            return s.strip() if isinstance(s, str) else str(s).strip()

        addr1 = normalize_string(val.get("addr1"))
        addr2 = normalize_string(val.get("addr2"))
        city = normalize_string(val.get("city"))
        state = normalize_string(val.get("state"))
        zip = normalize_string(val.get("zip"))
        country = normalize_string(val.get("country"))

        # Validate required fields
        if not (addr1 and city and state and zip):
            raise ValueError("Address missing required fields")

        # Build final payload: include optionals only if non-empty
        val_formatted = {"addr1": addr1, "city": city, "state": state, "zip": zip}
        if addr2:
            val_formatted["addr2"] = addr2
        if country:
            val_formatted["country"] = country

        return val_formatted

    @staticmethod
    def format_number(val: Any) -> int | float:
        """
        Helper method to ensure MailChimp number format is met

        :param val: number value to normalize
        :return:  int or float
        """
        # handles any bool vals (bool is subclass of int...)
        if isinstance(val, bool):
            raise ValueError("Boolean is not a valid number")
        # if already int or float, good to go
        if isinstance(val, (int, float)):
            return val
        # if string
        if isinstance(val, str):
            val_formatted = val.strip()
            if val_formatted == "":
                raise ValueError("Empty string is not a valid number")
            try:
                # check if int or float val
                return (
                    int(val_formatted)
                    if val_formatted.isdigit()
                    or (
                        (val_formatted.startswith("-") or val_formatted.startswith("+"))
                        and val_formatted[1:].isdigit()
                    )
                    else float(val_formatted)
                )
            except ValueError:
                pass
        raise ValueError(f"Not a valid number: {val}")
