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

    base_service_desk_endpoint = "rest/servicedeskapi/servicedesk"

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

        data["http_status_code"] = response.status_code

        return data

    # def get_jira_issue_url(self, issue_key: str) -> str:
    #     return f"{self.base_url}/rest/api/3/issue/{issue_key}/"

    def get_issue_types(self, project_id: str) -> list[dict]:
        return self.get(
            "rest/api/3/issuetype/project",
            params={"projectId": project_id},
            override_data_printing=True,
        )

    def get_service_desks(self) -> dict:
        return self.get(self.base_service_desk_endpoint, override_data_printing=True)

    def find_or_create_user(
        self, email_address: str, first_name: str, last_name: str
    ) -> int:
        existing_user = self.get(
            "rest/api/3/user/search", params={"query": email_address}
        )

        if existing_user and len(existing_user) > 0:
            return existing_user[0].get("accountId")

        new_user = self.post(
            "rest/servicedeskapi/customer",
            payload={
                "email": email_address,
                "displayName": f"{first_name} {last_name}",
            },
            override_data_printing=True
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
        service_desk_response = self.get_service_desks()
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

        issue_type_response = self.get_issue_types(service_desk_id)
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


# def send_transition_to_jira_by_name(issue_key, to_status_name):
#     base_url = get_jira_issue_url(issue_key)
#     url = f"{base_url}/transitions"
#     headers = get_jira_headers()

#     try:
#         issue_response = requests.get(base_url, headers=headers).json()
#         if (
#             issue_response.get("fields", {}).get("status", {}).get("name")
#             == to_status_name
#         ):
#             print("Ticket already in correct status")
#             return
#     except Exception as e:
#         raise e

#     try:
#         transition_list_response = requests.get(url, headers=headers).json()
#         transitions = transition_list_response.get("transitions", [])

#         for transition in transitions:
#             transition_to_name = transition["to"]["name"]
#             if transition_to_name == to_status_name:
#                 transition_id = int(transition["id"])
#                 return send_transition_to_jira(issue_key, transition_id)

#         raise ValueError(f"No transition named {to_status_name} in list {transitions}")
#     except Exception as e:
#         print(f"Unable to find transition to {to_status_name} on issue {issue_key}")
#         raise e


# def send_transition_to_jira(issue_key, jira_transition_id):
#     body_data = {"transition": {"id": jira_transition_id}}
#     base_url = get_jira_issue_url(issue_key)
#     url = f"{base_url}/transitions"
#     headers = get_jira_headers()

#     response = requests.post(url, json=body_data, headers=headers)

#     if response.status_code != 204:
#         raise ValueError(f"Error sending transition to Jira: {response.status_code}")
