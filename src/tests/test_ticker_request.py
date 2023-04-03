import os
import unittest
from unittest.mock import patch, MagicMock

import requests

from src.stac_utils.ticker_request import TickerRequest, TickerException, TickerAuthException


class TestTickerRequest(unittest.TestCase):
    def setUp(self) -> None:
        self.test_auth = {"TICKER_URL": "https://www.foo.bar", "AUTH_USER": "spam", "AUTH_PASS": "spam1234"}

    def test_init(self):
        """Test init"""
        with patch.dict(os.environ, values=self.test_auth):
            TickerRequest()

    def test_init_no_auth(self):
        """Test init with missing auth"""

        self.assertRaises(TickerAuthException, TickerRequest)

    def test_create_session(self):
        """Test create session"""

        with patch.dict(os.environ, values=self.test_auth):
            test_ticker = TickerRequest()
            test_session = test_ticker.create_session()
            self.assertIsInstance(test_session, requests.Session)
            self.assertEqual(test_session.auth, (self.test_auth["AUTH_USER"], self.test_auth["AUTH_PASS"]))

    def test_transform_response(self):
        """Test transform response"""

        test_response = requests.Response()
        with patch.dict(os.environ, values=self.test_auth):
            test_ticker = TickerRequest()
            self.assertIs(test_response, test_ticker.transform_response(test_response))

    def test_check_for_error_when_exists(self):
        """Test check for error when one exists"""

        test_response = requests.Response()
        test_response.status_code = 500

        with patch.dict(os.environ, values=self.test_auth):
            test_ticker = TickerRequest()
            self.assertRaises(TickerException, lambda: test_ticker.check_for_error(test_response, {}))

    def test_check_for_error_when_not_exists(self):
        """Test check for error when one does not exist"""

        test_response = requests.Response()
        test_response.status_code = 200

        with patch.dict(os.environ, values=self.test_auth):
            test_ticker = TickerRequest()
            test_ticker.check_for_error(test_response, {})

    def test_add_data(self):
        """Test add data"""

        with patch.dict(os.environ, values=self.test_auth):
            test_ticker = TickerRequest()
            test_data = {"state": "UNK", "source": "foo", "task": "bar", "metric": "spam", "amount": 42.0}
            test_ticker.add_data(**test_data)

            self.assertListEqual(test_ticker.data, [test_data])

    def test_send_to_ticker(self):
        """Test send to ticker"""

        with patch.dict(os.environ, values=self.test_auth):
            test_ticker = TickerRequest()
            test_ticker.post = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            test_ticker.post.return_value = mock_response
            test_data = {"state": "UNK", "source": "foo", "task": "bar", "metric": "spam", "amount": 42.0}
            test_ticker.add_data(**test_data)
            test_response = test_ticker.send_to_ticker()

            test_ticker.post.assert_called_once_with("/ticker", body=[test_data])
            self.assertIs(test_response, mock_response)
            self.assertListEqual(test_ticker.data, [])

    def test_send_to_ticker_no_data(self):
        """Test send to ticker with no data"""

        with patch.dict(os.environ, values=self.test_auth):
            test_ticker = TickerRequest()
            test_ticker.post = MagicMock()
            test_response = test_ticker.send_to_ticker()
            self.assertIsNone(test_response)
            test_ticker.post.assert_not_called()

    def test_send_to_ticker_with_error(self):
        """Test send to ticker when error happens"""

        with patch.dict(os.environ, values=self.test_auth):
            test_ticker = TickerRequest()
            test_ticker.post = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            test_ticker.post.return_value = mock_response
            test_data = {"state": "UNK", "source": "foo", "task": "bar", "metric": "spam", "amount": 42.0}
            test_ticker.add_data(**test_data)
            self.assertRaises(TickerException, test_ticker.send_to_ticker)

            test_ticker.post.assert_called_once_with("/ticker", body=[test_data])
            self.assertListEqual(test_ticker.data, [test_data])


if __name__ == "__main__":
    unittest.main()
