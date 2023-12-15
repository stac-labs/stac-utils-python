import os
import unittest

import requests

from unittest.mock import MagicMock, patch

from src.stac_utils.jira import JiraClient


class TestReachClient(unittest.TestCase):
    def setUp(self) -> None:
        self.test_client = JiraClient("foo", "bar", "https://example.atlassian.net")

    def test_init_env_keys(self):
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

