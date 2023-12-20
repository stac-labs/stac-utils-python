import os
import unittest

import requests

from json.decoder import JSONDecodeError
from unittest.mock import MagicMock, patch

from src.stac_utils.jira import JiraClient


class TestJiraClient(unittest.TestCase):
    def setUp(self) -> None:
        self.test_client = JiraClient("foo", "bar", "https://example.atlassian.net")

    def test_init_env_keys(self):
        """Test client initiated"""
        test_api_user = "foo"
        test_api_key = "bar"
        test_base_url = "https://example.atlassian.net"

        with patch.dict(
            os.environ,
            values={
                "JIRA_API_USER": test_api_user,
                "JIRA_API_KEY": test_api_key,
                "JIRA_BASE_URL": test_base_url,
            },
        ):
            test_client = JiraClient()
            self.assertEqual(test_api_user, test_client.api_user)
            self.assertEqual(test_api_key, test_client.api_key)

    def test_create_session(self):
        """Test session has api keys"""

        test_api_user = "foo"
        test_api_key = "bar"
        test_base_url = "https://example.atlassian.net"

        test_client = JiraClient(test_api_user, test_api_key, test_base_url)
        self.assertEqual(
            (test_api_user, test_api_key),
            test_client.session.auth,
        )

    def test_transform_response(self):
        """Test transform response handles normal data"""

        mock_data = {"fooBar": "spam"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "foo.bar/spam"
        mock_response.headers = {"user-agent": "nee"}
        mock_response.json = MagicMock(return_value=mock_data)

        test_data = self.test_client.transform_response(mock_response)
        self.assertEqual({"fooBar": "spam"}, test_data)

    def test_transform_response_when_no_json(self):
        """Test transform response handles 204 with no body"""

        mock_side_effect = JSONDecodeError("Expecting value", "foo", 1)
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.url = "foo.bar/spam"
        mock_response.headers = {"user-agent": "nee"}
        mock_response.json = MagicMock(side_effect=mock_side_effect)

        test_data = self.test_client.transform_response(mock_response)
        self.assertEqual({}, test_data)

    def test_transform_response_when_no_json_but_not_204(self):
        """Test transform response handles non-204 with no body"""

        mock_side_effect = JSONDecodeError("Expecting value", "foo", 0)
        mock_response = MagicMock()
        mock_response.status_code = 42
        mock_response.url = "foo.bar/spam"
        mock_response.headers = {"user-agent": "nee"}
        mock_response.json = MagicMock(side_effect=mock_side_effect)

        test_data = self.test_client.transform_response(mock_response)
        self.assertEqual(
            {
                "errors": "Expecting value: line 1 column 1 (char 0)",
                "http_status_code": 42,
            },
            test_data,
        )

    def test_transform_response_exception(self):
        """Test transform response handles exception in the response"""

        mock_response = MagicMock()
        mock_response.status_code = 42
        mock_response.json = MagicMock(side_effect=Exception("foo"))

        test_data = self.test_client.transform_response(mock_response)
        self.assertEqual({"errors": "foo", "http_status_code": 42}, test_data)

    def test_get_issue_urls(self):
        """Test issue-specific endpoints are correctly generated"""

        test_issue_key = "ABC-1"
        self.assertEqual(
            "rest/api/3/issue/ABC-1", self.test_client.get_issue_url(test_issue_key)
        )

        self.assertEqual(
            "rest/api/3/issue/ABC-1/transitions",
            self.test_client.get_issue_transitions_url(test_issue_key),
        )
