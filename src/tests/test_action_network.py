import os
import unittest
from unittest.mock import MagicMock, patch

from src.stac_utils.action_network import ActionNetworkClient


class TestActionNetworkClient(unittest.TestCase):
    def setUp(self) -> None:
        self.test_client = ActionNetworkClient()

    def test_init_env_keys(self):
        """Test that client initializes with environmental keys"""
        test_api_token = "foo"

        with patch.dict(os.environ, values={"ACTIONNETWORK_API_TOKEN": test_api_token}):
            test_client = ActionNetworkClient()
            self.assertEqual(test_api_token, test_client.api_token)

    def test_create_session(self):
        """Make sure API token and content type set in headers"""
        test_client = ActionNetworkClient("foo")
        self.assertTrue(
            {
                "OSDI-API-Token": test_client.api_token,
                "Content-Type": "application/json",
            }.items()
            <= test_client.session.headers.items(),
        )

    def test_transform_response(self):
        """Test that response is transformed and includes status code"""
        mock_data = {"foo_bar": "spam"}
        mock_response = MagicMock()
        mock_response.status_code = 42
        mock_response.json = MagicMock(return_value=mock_data)

        test_data = self.test_client.transform_response(mock_response)
        self.assertEqual({"foo_bar": "spam", "status_code": 42}, test_data)

    def test_check_response_for_rate_limit(self):
        """Test that response has rate limit of 1"""
        test_client = ActionNetworkClient("foo")
        self.assertEqual(1, test_client.check_response_for_rate_limit(None))
