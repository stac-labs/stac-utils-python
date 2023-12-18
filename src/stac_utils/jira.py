import logging
import os

import requests

from .http import HTTPClient

logger = logging.getLogger(__name__)


class JiraClient(HTTPClient):
    """
    Jira Client class built on basic HTTP Client class

    Parameters
    ==========
    api_user: username, will pick up "JIRA_API_USER" if it's in the environment
    api_key: the API key, will pick up "JIRA_API_KEY" if it's in the environment
    base_url: organization's Jira URL, will pick up "JIRA_BASE_URL" if it's in the environment
    """

    def __init__(
        self,
        api_user: str = None,
        api_key: str = None,
        base_url: str = None,
        *args,
        **kwargs,
    ):
        self.api_user = api_user or os.environ.get("JIRA_API_USER")
        self.api_key = api_key or os.environ.get("JIRA_API_KEY")
        self.base_url = base_url or os.environ.get("JIRA_BASE_URL")

        super().__init__(*args, **kwargs)

    def create_session(self) -> requests.Session:
        """
        Creates and returns session
        """
        headers = {
            "X-Atlassian-Token": "nocheck",
            "Accept": "application/json",
        }
        session = requests.Session()
        session.headers.update(headers)
        session.auth = (self.api_user, self.api_key)

        return session

    def transform_response(self, response: requests.Response, **kwargs):
        """Transforms the response from the API to JSON"""

        try:
            data = response.json() or {}
        except Exception as E:
            data = {"errors": str(E), "http_status_code": response.status_code}

        return data

    @staticmethod
    def get_issue_url(issue_key: str) -> str:
        """Returns the API end point to GET an issue"""
        return f"rest/api/3/issue/{issue_key}"

    def get_issue_transitions_url(self, issue_key: str) -> str:
        """
        Returns the API end point to GET the transitions now
        possible for an issue, given its current status
        """
        return f"{self.get_issue_url(issue_key)}/transitions"
