import os
import unittest
from unittest.mock import MagicMock, patch, call

from src.stac_utils.ngpvan import NGPVANClient, NGPVANException, NGPVANLocationException


class TestNGPVAN(unittest.TestCase):
    def setUp(self) -> None:
        self.test_client = NGPVANClient(mode=1)

    def test_init(self):
        """Test that client intiates"""

        NGPVANClient(mode=0)
        NGPVANClient(mode=1)

    def test_init_bad_mode(self):
        """Test that client fails if bad mode is given"""

        self.assertRaises(AssertionError, NGPVANClient, mode=42)

    def test_init_env_keys(self):
        """Test keys are pulled from env if not present"""

        test_mode = 1
        test_app = "foo"
        test_key = "bar"

        with patch.dict(os.environ, values={"NGPVAN_APP_NAME": test_app, "NGPVAN_API_KEY": test_key}):
            test_client = NGPVANClient(mode=test_mode)
            self.assertEqual(test_client.app_name, test_app)
            self.assertEqual(test_client.api_key, f"{test_key}|{test_mode}")

    def test_create_session(self):
        """Test session has api keys"""

        test_mode = 1
        test_app = "foo"
        test_key = "bar"
        test_client = NGPVANClient(mode=test_mode, app_name=test_app, api_key=test_key)
        self.assertEqual(test_client.session.auth, (test_app, f"{test_key}|{test_mode}"))

    def test_check_response_for_rate_limit(self):
        """Test that it returns 2"""

        self.assertEqual(self.test_client.check_response_for_rate_limit(None), 2)

    def test_transform_response(self):
        """Test transform response handles normal data"""

    def test_transform_response_headers(self):
        """Test transform response returns headers"""

    def test_transform_response_snake_case(self):
        """Test transform response transforms key names into snake case"""

    def test_transform_response_request_exception(self):
        """Test transform response handles exception in the response"""

    def test_transform_response_json_decoder_error(self):
        """Test transform response handles bad json data"""

    def test_transform_response_other_exception(self):
        """Test transform response handles something else going wrong"""

    def test_check_for_error(self):
        """Test check for error finds no error when no error is present"""

        test_data = {"foo": "bar"}
        self.test_client.check_for_error(None, test_data)

    def test_check_for_error_with_errors(self):
        """Test check for error finds an non-location error when included"""

        test_data = {"errors": [{"text": "foo"}]}
        mock_response = MagicMock()
        mock_response.content = "bar"
        self.assertRaises(NGPVANException, self.test_client.check_for_error, mock_response, test_data)

    def test_check_for_error_with_location_errors(self):
        """Test check for error finds a location error"""

        location_error_text = "'location' is required by the specified Event"
        test_data = {"errors": [{"text": location_error_text}]}
        self.assertRaises(NGPVANLocationException, self.test_client.check_for_error, None, test_data, True)

    def test_get_paginated_items(self):
        """Test it pages through multiple urls"""

    def test_get_paginated_items_one_page(self):
        """Test it pages through one page"""


if __name__ == "__main__":
    unittest.main()
