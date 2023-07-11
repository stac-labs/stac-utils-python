import os
import unittest

import requests

from unittest.mock import MagicMock, patch, call

from src.stac_utils.reach import ReachClient


class TestReachClient(unittest.TestCase):
    def setUp(self) -> None:
        self.test_client = ReachClient("foo", "bar")

    def test_init_env_keys(self):
        test_api_user = "foo"
        test_api_password = "bar"

        with patch.dict(
            os.environ,
            values={
                "REACH_API_USER": test_api_user,
                "REACH_API_PASSWORD": test_api_password,
            },
        ):
            test_client = ReachClient()
            self.assertEqual(test_api_user, test_client.api_user)
            self.assertEqual(test_api_password, test_client.api_password)
            self.assertIsNone(test_client.access_token)

    @patch("requests.Session")
    def test_refresh_auth(self, mock_session):
        mock_session.return_value.post.return_value.text = """
        {"access_token": "foo"}"""
        test_client = ReachClient("foo", "bar")
        test_client.refresh_auth(None)
        self.assertEqual(test_client.access_token, "foo")
        test_body = {
            "username": test_client.api_user,
            "password": test_client.api_password,
        }
        endpoint = "/oauth/token"
        mock_session.return_value.post.assert_called_once_with(
            test_client.base_url + endpoint, data=test_body
        )

    def test_create_session(self):
        class ReachClientWithMockAuth(ReachClient):
            def refresh_auth(self, response: requests.Response):
                self.access_token = "foo"

        test_client = ReachClientWithMockAuth("foo", "bar")

        self.assertTrue(
            {
                "Authorization": "Bearer foo",
            }.items()
            <= test_client.session.headers.items(),
        )

    def test_create_session_with_access_token(self):
        test_client = ReachClient("foo", "bar")
        test_client.access_token = "spam"
        test_client.refresh_auth = MagicMock()
        test_client.create_session()
        test_client.refresh_auth.assert_not_called()
