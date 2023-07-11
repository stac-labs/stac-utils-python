import json
import logging
import os

import requests

from .http import HTTPClient

logger = logging.getLogger(__name__)


class ReachClient(HTTPClient):
    base_url = "https://api.reach.vote/api/v1"

    def __init__(self, api_user: str = None, api_password: str = None, *args, **kwargs):
        self.api_user = api_user or os.environ["REACH_API_USER"]
        self.api_password = api_password or os.environ["REACH_API_PASSWORD"]
        self.access_token = None
        super().__init__(*args, **kwargs)

    def refresh_auth(self, response: requests.Response):
        body = {
            "username": self.api_user,
            "password": self.api_password,
        }
        endpoint = "/oauth/token"
        session = requests.Session()
        response = session.post(self.base_url + endpoint, data=body)
        self.access_token = json.loads(response.text)["access_token"]

    def create_session(self) -> requests.Session:
        """Create a session, set headers & auth"""
        if not self.access_token:
            self.refresh_auth(None)

        session = requests.Session()
        headers = {"Authorization": "Bearer " + self.access_token}
        session.headers.update(headers)
        return session

