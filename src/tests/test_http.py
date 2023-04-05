import unittest
from itertools import product
from unittest.mock import MagicMock, patch, call

import requests

from src.stac_utils.http import Client, HTTPClient


class MockClient(Client):
    """Non-abstract version of Client so we can test its non-abstract methods"""

    def create_session(self):
        return MagicMock()

    def call_api(self, *args, **kwargs):
        pass

    def transform_response(self, *args, **kwargs):
        pass

    def check_for_error(self, *args, **kwargs):
        pass


class TestClient(unittest.TestCase):
    def test_init(self):
        """Test init raises type error because it's an abstract class"""

        self.assertRaises(TypeError, Client)


class TestMockClient(unittest.TestCase):
    def test_init_not_abstract(self):
        """Test init with non-abstract"""

        MockClient()

    def test_session_context(self):
        """Test session context manager"""

        test_client = MockClient()

        with test_client.session as test_session:
            first_session = test_session
            self.assertIsInstance(test_session, MagicMock)
            with test_client.session as test_session2:
                self.assertIs(test_session, test_session2)

        with test_client.session as test_session3:
            self.assertIs(first_session, test_session3)

    def test_session_property(self):
        """Test session property"""

        test_client = MockClient()
        self.assertIsNone(test_client._session)

        test_session = test_client.session
        self.assertIsInstance(test_session, MagicMock)


class TestHTTPClient(unittest.TestCase):
    def test_init(self):
        """Test init"""

        HTTPClient()

    def test_rate_limits(self):
        """Test rate limits"""

        test_client = HTTPClient()
        test_client.update_rate_limits = MagicMock(return_value={})

        _ = test_client.rate_limits
        test_client.update_rate_limits.assert_called_once()

        # second time it should be cached
        _ = test_client.rate_limits
        test_client.update_rate_limits.assert_called_once()

    @patch("time.sleep")
    def test_wait_for_rate(self, mock_sleep: MagicMock):
        """Test wait for rate limits"""

        test_client = HTTPClient()

        test_client.check_response_for_rate_limit = MagicMock(return_value=0.42)
        test_response = MagicMock()

        test_client.wait_for_rate("FOO", test_response)
        # should return with value from check_response_for_rate_limit
        mock_sleep.assert_called_once_with(0.42)

    @patch("time.sleep")
    def test_wait_for_rate_no_limit_in_response(self, mock_sleep: MagicMock):
        """Test wait for rate limit when there's no rate limit in response"""

        test_client = HTTPClient()
        test_client._rate_limits = {"FOO": (1.0, 1.0)}

        test_client.check_response_for_rate_limit = MagicMock(return_value=None)
        test_response = MagicMock()

        test_client.wait_for_rate("FOO", test_response)
        # should return with value from rate_limits * 60
        mock_sleep.assert_called_once_with(60.0)

    @patch("time.sleep")
    def test_wait_for_rate_default_wait(self, mock_sleep: MagicMock):
        """Test wait for default rate limit"""

        test_client = HTTPClient()
        test_client.check_response_for_rate_limit = MagicMock(return_value=None)
        test_response = MagicMock()

        test_client.wait_for_rate("FOO", test_response)
        # should return with value from retry_wait
        mock_sleep.assert_called_once_with(test_client.retry_wait)

    def test_check_response_for_rate_limit(self):
        """Test check response for rate limit"""

        mock_response = MagicMock()
        test_client = HTTPClient()
        result_rate_limit = test_client.check_response_for_rate_limit(mock_response)
        self.assertIsNone(result_rate_limit)

    def test_format_url(self):
        """Test format url"""

        test_base_urls = ["https://foo.org", "https://foo.org/"]
        test_endpoints = [
            "bar",
            "/bar",
            "/bar/",
            "bar/",
        ]
        expected_url = "https://foo.org/bar"

        for test_base_url, test_endpoint in product(test_base_urls, test_endpoints):
            test_client = HTTPClient()
            test_client.base_url = test_base_url
            result_url = test_client.format_url(test_endpoint)
            self.assertEqual(expected_url, result_url)

    @patch("time.sleep")
    def test_call_api(self, mock_sleep: MagicMock):
        """Test call api"""

        test_client = HTTPClient()
        test_session = test_client.session
        test_response = MagicMock()
        test_response.status_code = 200
        test_response.content = {}
        test_session.request = MagicMock(return_value=test_response)

        test_client.call_api("GET", "/foo")
        test_session.request.assert_called_once_with(
            "GET", "ERROR/foo", params=None, json=None
        )
        mock_sleep.assert_called_once_with(0.0)

    def test_call_api_with_404(self):
        """Test call api with 404 exception"""

        test_client = HTTPClient()

        test_session = test_client.session
        test_response = MagicMock()
        test_response.status_code = 404
        test_response.content = {}
        test_response.raise_for_status = MagicMock(
            side_effect=requests.exceptions.RequestException
        )
        test_session.request = MagicMock(return_value=test_response)

        self.assertRaises(
            requests.exceptions.RequestException, test_client.call_api, "GET", "/foo"
        )

    @patch("time.sleep")
    def test_call_api_with_429(self, mock_sleep: MagicMock):
        """Test call api with hitting rate limit"""

        test_client = HTTPClient()
        test_client.retry_wait = 1.0
        test_client.retry_limit = 3
        test_client.wait_for_rate = MagicMock()

        test_session = test_client.session
        test_response = MagicMock()
        test_response.status_code = 429
        test_response.content = {}
        test_response.raise_for_status = MagicMock(
            side_effect=requests.exceptions.RequestException
        )
        test_session.request = MagicMock(return_value=test_response)

        self.assertRaises(
            requests.exceptions.RequestException, test_client.call_api, "GET", "/foo"
        )
        test_client.wait_for_rate.assert_called()
        mock_sleep.assert_called()

    @patch("time.sleep")
    def test_call_api_with_401(self, mock_sleep: MagicMock):
        """Test call api with expired auth"""

        test_client = HTTPClient()
        test_client.refresh_auth = MagicMock()
        test_client.retry_wait = 1.0
        test_client.retry_limit = 3

        test_session = test_client.session
        test_response = MagicMock()
        test_response.status_code = 401
        test_response.content = {}
        test_response.raise_for_status = MagicMock(
            side_effect=requests.exceptions.RequestException
        )
        test_session.request = MagicMock(return_value=test_response)

        self.assertRaises(
            requests.exceptions.RequestException, test_client.call_api, "GET", "/foo"
        )
        test_client.refresh_auth.assert_called()
        mock_sleep.assert_has_calls([call(0.0), call(2.0)])

    @patch("time.sleep")
    def test_call_api_with_connection_error(self, mock_sleep: MagicMock):
        """Test call api with status code free connection error"""

        test_client = HTTPClient()
        test_client.refresh_auth = MagicMock()
        test_client.retry_wait = 1.0
        test_client.retry_limit = 3

        test_session = test_client.session
        test_response = MagicMock()
        test_response.status_code = None
        test_response.raise_for_status = MagicMock(
            side_effect=requests.exceptions.RequestException
        )
        test_session.request = MagicMock(return_value=test_response)

        self.assertRaises(
            requests.exceptions.RequestException, test_client.call_api, "GET", "/foo"
        )
        mock_sleep.assert_has_calls([call(0.0), call(1.0), call(2.0), call(3.0)])

    def test_get(self):
        """Test GET"""
        test_client = HTTPClient()
        test_client.call_api = MagicMock()

        test_client.get()
        test_client.call_api.assert_called_once_with("GET")

    def test_post(self):
        """Test POST"""
        test_client = HTTPClient()
        test_client.call_api = MagicMock()

        test_client.post()
        test_client.call_api.assert_called_once_with("POST")

    def test_put(self):
        """Test PUT"""
        test_client = HTTPClient()
        test_client.call_api = MagicMock()

        test_client.put()
        test_client.call_api.assert_called_once_with("PUT")

    def test_patch(self):
        """Test PATCH"""
        test_client = HTTPClient()
        test_client.call_api = MagicMock()

        test_client.patch()
        test_client.call_api.assert_called_once_with("PATCH")

    def test_delete(self):
        """Test DELETE"""
        test_client = HTTPClient()
        test_client.call_api = MagicMock()

        test_client.delete()
        test_client.call_api.assert_called_once_with("DELETE")

    def test_update(self):
        """Test UPDATE"""
        test_client = HTTPClient()
        test_client.call_api = MagicMock()

        test_client.update()
        test_client.call_api.assert_called_once_with("UPDATE")

    def test_update_rate_limits(self):
        """Test update rate limits"""
        test_client = HTTPClient()
        test_rate_limits = test_client.update_rate_limits()
        self.assertDictEqual(test_rate_limits, {})

    def test_create_session(self):
        """Test create session"""
        test_client = HTTPClient()
        test_session = test_client.create_session()
        self.assertIsInstance(test_session, requests.Session)

    def test_transform_response(self):
        """Test transform_response"""
        test_client = HTTPClient()
        mock_response = MagicMock()
        expected_transform = "FOO"
        mock_response.content = expected_transform
        result_transform = test_client.transform_response(mock_response)
        self.assertEqual(result_transform, expected_transform)


if __name__ == "__main__":
    unittest.main()
