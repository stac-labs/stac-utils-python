import os
import json
import requests
from stac_utils.http import HTTPClient


ROW_LIMIT = 10000


class ActionnetworkClient(HTTPClient):
    base_url = "https://actionnetwork.org/api/v2"

    def __init__(self, api_token: str = None, *args, **kwargs):
        self.api_token = api_token or os.environ.get("ACTIONNETWORK_API_TOKEN")
        super().__init__(*args, **kwargs)

    def create_session(self) -> requests.Session:
        headers = {"OSDI-API-Token": self.api_token, "Content-Type": "application/json"}
        session = requests.Session()
        session.headers.update(headers)
        return session

    def transform_response(self, response: requests.Response, **kwargs) -> dict:
        try:
            data = response.json() or {}
        except json.decoder.JSONDecodeError:
            data = {}
        data["status_code"] = response.status_code
        return data

    def check_response_for_rate_limit(
        self, response: requests.Response
    ) -> [int, float, None]:
        return 1
