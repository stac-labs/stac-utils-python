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
        """Transform the response from the API to JSON"""

        try:
            data = response.json() or {}
        except Exception as E:
            data = {"errors": str(E)}

        return data

    def get_issue_url(self, issue_key: str) -> str:
        return f"rest/api/3/issue/{issue_key}/"

    def get_issue(self, issue_key: str, **kwargs) -> dict:
        self.get(self.get_issue_url(issue_key), **kwargs)

    def get_issue_transitions(self, issue_key: str, **kwargs) -> dict:
        self.get(f"{self.get_issue_url(issue_key)}/transitions", **kwargs)

    def get_issue_types(self, project_id: str, **kwargs) -> list[dict]:
        return self.get(
            "rest/api/3/issuetype/project", params={"projectId": project_id}, **kwargs
        )

    def get_service_desks(self, **kwargs) -> dict:
        return self.get("rest/servicedeskapi/servicedesk", **kwargs)

    def post_issue_transitions(self, issue_key: str, transition_id: int) -> dict:
        return self.post(
            f"{self.get_issue_url(issue_key)}/transitions",
            body={"transition": {"id": transition_id}},
        )

    def find_or_create_user(
        self, email_address: str, first_name: str, last_name: str
    ) -> int:
        existing_user = self.get(
            "rest/api/3/user/search",
            params={"query": email_address},
            override_data_printing=True,
        )

        if existing_user and len(existing_user) > 0:
            return existing_user[0].get("accountId")

        new_user = self.post(
            "rest/servicedeskapi/customer",
            payload={
                "email": email_address,
                "displayName": f"{first_name} {last_name}",
            },
            override_data_printing=True,
        )

        return new_user.get("accountId")

    ## TODO move this back to the other repo?
    def build_create_issue_payload(
        self,
        jira_board: str,
        summary: str,
        reporter_email: str,
        reporter_first_name: str,
        reporter_last_name: str,
        issue_type_lookup: str = "Task",
        reporter_id: int = None,
    ) -> dict:
        service_desk_response = self.get_service_desks(override_data_printing=True)
        service_desk = [
            board
            for board in service_desk_response.get("values")
            if board["projectKey"] == jira_board
        ]

        if len(service_desk) != 1:
            raise ValueError(
                f"Could not find a single service desk matching key '{jira_board}'"
            )

        service_desk_id = service_desk[0].get("projectId")

        issue_type_response = self.get_issue_types(
            service_desk_id, override_data_printing=True
        )
        issue_type = [
            it for it in issue_type_response if it.get("name") == issue_type_lookup
        ]

        if len(issue_type) != 1:
            raise ValueError(
                f"Could not find a single issue type matching '{issue_type_lookup}' in this service desk"
            )

        if reporter_id is None:
            reporter_id = self.find_or_create_user(
                reporter_email,
                reporter_first_name,
                reporter_last_name,
            )

        return {
            "fields": {
                "summary": summary,
                "issuetype": {"id": issue_type[0].get("id")},
                "project": {"id": service_desk_id},
                "reporter": {"id": reporter_id},
            }
        }

    def post_create_issue(self, payload: dict) -> dict:
        return self.post("rest/api/3/issue", body=payload)

    def send_transition_to_jira_by_name(self, issue_key: str, to_status_name: str):
        issue_response = self.get_issue(issue_key, override_data_printing=True)
        if (
            issue_response.get("fields", {}).get("status", {}).get("name")
            == to_status_name
        ):
            logger.info("Ticket already in correct status")
            return

        transition_list_response = self.get_issue_transitions(
            issue_key, override_data_printing=True
        )
        transitions = transition_list_response.get("transitions", [])

        transition = [
            t for t in transitions if t.get("to", {}).get("name") == to_status_name
        ]

        if len(transition) < 1:
            raise ValueError(
                f"Could not find a transition to {to_status_name} for {issue_key}"
            )

        return self.post_issue_transitions(
            issue_key,
            int(transition[0].get("id")),
        )
