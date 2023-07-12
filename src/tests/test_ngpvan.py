import json
import os
import unittest
from unittest.mock import MagicMock, patch, call

import requests

from src.stac_utils.ngpvan import NGPVANClient, NGPVANException, NGPVANLocationException


class TestNGPVAN(unittest.TestCase):
    def setUp(self) -> None:
        self.test_client = NGPVANClient(mode=1)

    def test_init(self):
        """Test that client initiates"""

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

        with patch.dict(
            os.environ, values={"NGPVAN_APP_NAME": test_app, "NGPVAN_API_KEY": test_key}
        ):
            test_client = NGPVANClient(mode=test_mode)
            self.assertEqual(test_app, test_client.app_name)
            self.assertEqual(f"{test_key}|{test_mode}", test_client.api_key)

    def test_create_session(self):
        """Test session has api keys"""

        test_mode = 1
        test_app = "foo"
        test_key = "bar"
        test_client = NGPVANClient(mode=test_mode, app_name=test_app, api_key=test_key)
        self.assertEqual(
            (test_app, f"{test_key}|{test_mode}"),
            test_client.session.auth,
        )

    def test_check_response_for_rate_limit(self):
        """Test that it returns 2"""

        self.assertEqual(2, self.test_client.check_response_for_rate_limit(None))

    def test_transform_response(self):
        """Test transform response handles normal data"""

        mock_data = {"fooBar": "spam"}
        mock_response = MagicMock()
        mock_response.status_code = 42
        mock_response.url = "foo.bar/spam"
        mock_response.headers = {"user-agent": "nee"}
        mock_response.json = MagicMock(return_value=mock_data)

        test_data = self.test_client.transform_response(mock_response)
        self.assertEqual({"foo_bar": "spam", "http_status_code": 42}, test_data)

    def test_transform_response_no_dict(self):
        """Test transform response handles single value data"""

        mock_data = 1
        mock_response = MagicMock()
        mock_response.status_code = 42
        mock_response.url = "foo.bar/spam"
        mock_response.headers = {"user-agent": "nee"}
        mock_response.json = MagicMock(return_value=mock_data)

        test_data = self.test_client.transform_response(mock_response)
        self.assertEqual({"spam": 1, "http_status_code": 42}, test_data)

    def test_transform_response_headers(self):
        """Test transform response returns headers"""

        mock_data = {"fooBar": "spam"}
        mock_response = MagicMock()
        mock_response.status_code = 42
        mock_response.url = "foo.bar/spam"
        mock_response.headers = {"user-agent": "nee"}
        mock_response.json = MagicMock(return_value=mock_data)

        test_data = self.test_client.transform_response(
            mock_response, return_headers=True
        )
        self.assertEqual(
            {
                "foo_bar": "spam",
                "http_status_code": 42,
                "headers": {"user-agent": "nee"},
            },
            test_data,
        )

    def test_transform_response_no_snake_case(self):
        """Test transform response does not transform key names into snake case"""

        mock_data = {"fooBar": "spam"}
        mock_response = MagicMock()
        mock_response.status_code = 42
        mock_response.json = MagicMock(return_value=mock_data)

        test_data = self.test_client.transform_response(
            mock_response, use_snake_case=False
        )
        self.assertEqual({"fooBar": "spam", "http_status_code": 42}, test_data)

    def test_transform_response_request_exception(self):
        """Test transform response handles exception in the response"""

        mock_response = MagicMock()
        mock_response.status_code = 42
        mock_response.json = MagicMock(side_effect=requests.RequestException)

        test_data = self.test_client.transform_response(mock_response)
        self.assertEqual({"http_status_code": 42}, test_data)

    def test_transform_response_json_decoder_error(self):
        """Test transform response handles bad json data"""

        mock_response = MagicMock()
        mock_response.status_code = 42
        mock_response.json = MagicMock(
            side_effect=json.decoder.JSONDecodeError("foo", "bar", 42)
        )

        test_data = self.test_client.transform_response(mock_response)
        self.assertEqual({"http_status_code": 42}, test_data)

    def test_transform_response_other_exception(self):
        """Test transform response handles something else going wrong"""

        mock_response = MagicMock()
        mock_response.status_code = 42
        mock_response.json = MagicMock(side_effect=Exception("foo"))

        test_data = self.test_client.transform_response(mock_response)
        self.assertEqual({"errors": "foo", "http_status_code": 42}, test_data)

    def test_check_for_error(self):
        """Test check for error finds no error when no error is present"""

        test_data = {"foo": "bar"}
        self.test_client.check_for_error(None, test_data)

    def test_check_for_error_with_errors(self):
        """Test check for error finds an non-location error when included"""

        test_data = {"errors": [{"text": "foo"}]}
        mock_response = MagicMock()
        mock_response.content = "bar"
        self.assertRaises(
            NGPVANException, self.test_client.check_for_error, mock_response, test_data
        )

    def test_check_for_error_with_location_errors(self):
        """Test check for error finds a location error"""

        location_error_text = "'location' is required by the specified Event"
        test_data = {"errors": [{"text": location_error_text}]}
        self.assertRaises(
            NGPVANLocationException,
            self.test_client.check_for_error,
            None,
            test_data,
            True,
        )

    def test_get_paginated_items(self):
        """Test it pages through multiple urls"""

        mock_url = "foo.bar/spam"
        self.test_client.get = MagicMock(
            side_effect=[
                {"items": [{"foo": "bar"}], "next_page_link": mock_url},
                {"items": [{"foo": "bar"}], "next_page_link": mock_url},
                {"items": []},
            ]
        )
        self.assertListEqual(
            self.test_client.get_paginated_items("spam"),
            [{"foo": "bar"}, {"foo": "bar"}],
        )
        self.test_client.get.assert_has_calls(
            [call("spam"), call("spam"), call("spam")]
        )

    def test_get_paginated_items_one_page(self):
        """Test it pages through one page"""

        self.test_client.get = MagicMock(
            side_effect=[
                {"items": [{"foo": "bar"}]},
            ]
        )
        self.assertListEqual(
            self.test_client.get_paginated_items("spam"),
            [{"foo": "bar"}],
        )

    def test_format_person_json(self):

        self.assertEqual(
            NGPVANClient.format_person_json(
                {
                    "first_name": "John",
                    "last_name": "Smith",
                    "date_of_birth": "1984-01-01",
                    "custom_field_id": "42",
                    "custom_field_group_id": "42",
                    "van_id": "12345",
                    "email": "foo@bar.com",
                    "phone": "817-555-1234",
                    "middle_name": "Jacob",
                    "street_address": "123 Main",
                    "city": "Clinton",
                    "state": "IA",
                    "zip": "12345",
                },
                "van_id",
                True,
            ),
            {
                "firstName": "John",
                "lastName": "Smith",
                "dateOfBirth": "1984-01-01",
                "contactMode": "Person",
                "identifiers": [{"type": "votervanid", "externalId": "12345"}],
                "emails": [{"email": "foo@bar.com"}],
                "phones": [{"phoneNumber": "817-555-1234"}],
                "middleName": "Jacob",
                "addresses": [
                    {
                        "addressLine1": "123 Main",
                        "city": "Clinton",
                        "stateOrProvince": "IA",
                        "zipOrPostalCode": "12345",
                    }
                ],
            },
        )

        self.assertEqual(
            NGPVANClient.format_person_json(
                {
                    "first_name": "John",
                    "last_name": "Smith",
                    "date_of_birth": "1984-01-01",
                    "email": "foo@bar.com",
                    "phone": "817-555-1234",
                    "street_address": "123 Main",
                    "city": "Clinton",
                    "stateOrProvince": "IA",
                    "zipOrPostalCode": "12345",
                },
                "van_id",
                True,
            ),
            {
                "firstName": "John",
                "lastName": "Smith",
                "dateOfBirth": "1984-01-01",
                "contactMode": "Person",
                "identifiers": [{"type": "votervanid", "externalId": None}],
                "emails": [{"email": "foo@bar.com"}],
                "phones": [{"phoneNumber": "817-555-1234"}],
                "addresses": [
                    {
                        "addressLine1": "123 Main",
                        "city": "Clinton",
                        "stateOrProvince": "IA",
                        "zipOrPostalCode": "12345",
                    }
                ],
            },
        )

        self.assertEqual(
            NGPVANClient.format_person_json(
                {
                    "first_name": "John",
                    "last_name": "Smith",
                    "date_of_birth": "1984-01-01",
                },
                "van_id",
                True,
            ),
            {
                "firstName": "John",
                "lastName": "Smith",
                "dateOfBirth": "1984-01-01",
                "contactMode": "Person",
                "identifiers": [{"type": "votervanid", "externalId": None}],
                "addresses": [{}],
            },
        )


if __name__ == "__main__":
    unittest.main()
