import os
import unittest

from unittest.mock import MagicMock, patch, call

from src.stac_utils.bsd import BSDClient


class TestBSDClient(unittest.TestCase):
    def test_class(self):
        self.assertEqual(2, BSDClient.api_ver)

    def test_init_env_keys(self):
        """Test keys are pulled from env if not present"""

        test_base_url = "foo"
        test_bsd_api_id = "bar"
        test_bsd_api_secret = "spam"

        with patch.dict(
            os.environ,
            values={
                "BSD_URL": test_base_url,
                "BSD_API_ID": test_bsd_api_id,
                "BSD_API_SECRET": test_bsd_api_secret,
            },
        ):
            test_client = BSDClient()
            self.assertEqual(test_base_url, test_client.base_url)
            self.assertEqual(test_bsd_api_id, test_client.bsd_api_id)
            self.assertEqual(test_bsd_api_secret, test_client.bsd_api_secret)

    def test_init(self):
        test_base_url = "foo"
        test_bsd_api_id = "bar"
        test_bsd_api_secret = "spam"

        test_client = BSDClient(test_base_url, test_bsd_api_id, test_bsd_api_secret)
        self.assertEqual(test_base_url, test_client.base_url)
        self.assertEqual(test_bsd_api_id, test_client.bsd_api_id)
        self.assertEqual(test_bsd_api_secret, test_client.bsd_api_secret)

    def test_generate_api_mac(self):
        test_client = BSDClient("foo", "bar", "spam")
        result_api_mac = test_client.generate_api_mac("foo", "bar")
        self.assertEqual("a261038aae72b22be529eed3a9017c944d4a12d4", result_api_mac)

    @patch("time.time")
    @patch("src.stac_utils.bsd.super")
    def test_call_api(self, mock_super, mock_time):
        mock_time.return_value = 42
        test_client = BSDClient("foo", "bar", "spam")
        test_api_mac = "e87ae5f9b7fdfa4bdee5f6f120d2c42b6918a8eb"
        test_client.call_api("GET", "foo")

        test_params = {
            "api_ver": test_client.api_ver,
            "api_id": test_client.bsd_api_id,
            "api_ts": "42",
            "api_mac": test_api_mac,
        }

        mock_super().call_api.assert_called_once_with(
            "GET",
            "foo",
            params=test_params,
            body=None,
            return_headers=False,
            use_snake_case=True,
            override_error_logging=False,
            override_data_printing=False,
        )

    def test_transform_response(self):
        test_client = BSDClient("foo", "bar", "spam")
        test_response = MagicMock()
        test_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <api>
            <signup_form id="1" modified_dt="1267728690">
                <signup_form_name>Default Signup Form</signup_form_name>
                <signup_form_slug/>
                <form_public_title>This is the public form title</form_public_title>
                <create_dt>2010-02-08 18:33:11</create_dt>
            </signup_form>
            <signup_form id="3" modified_dt="1269523250">
                <signup_form_name>signup form</signup_form_name>
                <signup_form_slug>form</signup_form_slug>
                <form_public_title>This is a signup form</form_public_title>
                <create_dt>2010-03-25 13:20:50</create_dt>
            </signup_form>
        </api>"""

        expected_result = {
            "api": {
                "signup_form": [
                    {
                        "signup_form_name": "Default Signup Form",
                        "signup_form_slug": None,
                        "form_public_title": "This is the public form title",
                        "create_dt": "2010-02-08 18:33:11",
                    },
                    {
                        "signup_form_name": "signup form",
                        "signup_form_slug": "form",
                        "form_public_title": "This is a signup form",
                        "create_dt": "2010-03-25 13:20:50",
                    },
                ]
            }
        }

        self.assertEqual(expected_result, test_client.transform_response(test_response))
