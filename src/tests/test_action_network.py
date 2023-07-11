import os
import unittest
from unittest.mock import MagicMock, patch, call

from src.stac_utils.action_network import ActionNetworkClient


class TestActionNetworkClient(unittest.TestCase):
    def setUp(self) -> None:
        self.test_client = ActionNetworkClient()

    def test_init_env_keys(self):
        test_api_token = "foo"

        with patch.dict(os.environ, values={"ACTIONNETWORK_API_TOKEN": test_api_token}):
            test_client = ActionNetworkClient()
            self.assertEqual(test_api_token, test_client.api_token)

    def test_create_session(self):
        test_client = ActionNetworkClient("foo")
        self.assertTrue(
            {
                "OSDI-API-Token": test_client.api_token,
                "Content-Type": "application/json",
            }.items()
            <= test_client.session.headers.items(),
        )

    def test_transform_response(self):
        mock_data = {"foo_bar": "spam"}
        mock_response = MagicMock()
        mock_response.status_code = 42
        mock_response.json = MagicMock(return_value=mock_data)

        test_data = self.test_client.transform_response(mock_response)
        self.assertEqual({"foo_bar": "spam", "status_code": 42}, test_data)

    def test_check_response_for_rate_limit(self):
        test_client = ActionNetworkClient("foo")
        self.assertEqual(1, test_client.check_response_for_rate_limit(None))
