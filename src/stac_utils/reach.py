import json
import logging
import os

import requests

from .http import HTTPClient

logger = logging.getLogger(__name__)


class ReachClient(HTTPClient):
    """
    Reach Client class built on basic HTTP Client class

    Parameters
    ==========
    api_user: username, will pick up "REACH_API_USER" if it's in the environment
    api_password: password, will pick up "REACH_API_PASSWORD" if it's in the environment
    """

    base_url = "https://api.reach.vote/api/v1"
    actual_base_url = "https://api.reach.vote"

    def __init__(self, api_user: str = None, api_password: str = None, *args, **kwargs):
        self.api_user = api_user or os.environ["REACH_API_USER"]
        self.api_password = api_password or os.environ["REACH_API_PASSWORD"]
        self.access_token = None
        super().__init__(*args, **kwargs)

    def refresh_auth(self, response: requests.Response):
        """Refreshes authorization in case of no access token"""
        body = {
            "username": self.api_user,
            "password": self.api_password,
        }
        endpoint = "/oauth/token"
        session = requests.Session()
        response = session.post(self.actual_base_url + endpoint, data=body)
        self.access_token = json.loads(response.text)["access_token"]

    def create_session(self) -> requests.Session:
        """Create a session, set headers & auth"""
        if not self.access_token:
            self.refresh_auth(None)

        session = requests.Session()
        headers = {"Authorization": "Bearer " + self.access_token}
        session.headers.update(headers)
        return session
