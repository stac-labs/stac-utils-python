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
            },
        )

        self.assertEqual(
            NGPVANClient.format_person_json(
                {
                    "first_name": "John",
                    "last_name": "Smith",
                    "date_of_birth": "1984-01-01",
                },
                None,
                False,
            ),
            {
                "firstName": "John",
                "lastName": "Smith",
                "dateOfBirth": "1984-01-01",
                "contactMode": "Person",
            },
        )

        self.assertEqual(
            NGPVANClient.format_person_json(
                {
                    "first_name": "John",
                    "last_name": "Smith",
                    "date_of_birth": "1984-01-01",
                    "email": "foo@aol.com\t\t\t",
                },
                None,
                False,
            ),
            {
                "firstName": "John",
                "lastName": "Smith",
                "dateOfBirth": "1984-01-01",
                "emails": [{"email": "foo@aol.com"}],
                "contactMode": "Person",
            },
        )

        self.assertRaises(
            ValueError,
            NGPVANClient.format_person_json,
            {
                "first_name": "John",
                "last_name": "Smith",
                "date_of_birth": "1984-01-01",
            },
            None,
            True,
        )

        self.assertEqual(
            NGPVANClient.format_person_json(
                {
                    "first_name": "John",
                    "last_name": "Smith",
                    "date_of_birth": "1984-01-01",
                    "custom_field_id": "42",
                    "custom_field_group_id": "42",
                },
                "van_id",
                False,
            ),
            {
                "firstName": "John",
                "lastName": "Smith",
                "dateOfBirth": "1984-01-01",
                "contactMode": "Person",
                "customFieldValues": [
                    {
                        "custom_field_id": "42",
                        "custom_field_group_id": "42",
                        "assignedValue": None,
                    }
                ],
            },
        )

    """
    Tests for expanded format_person_json functionality.
    Copy these methods into the existing TestNGPVAN class.
    """

    # =========================================================================
    # Address Field Alias Tests
    # =========================================================================

    def test_format_person_json_address_alias(self):
        """Test that 'address' field is treated as street_address"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "address": "123 Main St",
                "city": "Clinton",
                "state": "IA",
                "zip": "12345",
            },
            None,
            False,
        )
        self.assertEqual(
            result["addresses"],
            [
                {
                    "addressLine1": "123 Main St",
                    "city": "Clinton",
                    "stateOrProvince": "IA",
                    "zipOrPostalCode": "12345",
                }
            ],
        )

    def test_format_person_json_address1_alias(self):
        """Test that 'address1' field is treated as street_address"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "address1": "456 Oak Ave",
                "city": "Clinton",
                "state": "IA",
                "zip": "12345",
            },
            None,
            False,
        )
        self.assertEqual(result["addresses"][0]["addressLine1"], "456 Oak Ave")

    def test_format_person_json_address_1_alias(self):
        """Test that 'address_1' field is treated as street_address"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "address_1": "789 Pine Rd",
                "city": "Clinton",
                "state": "IA",
                "zip": "12345",
            },
            None,
            False,
        )
        self.assertEqual(result["addresses"][0]["addressLine1"], "789 Pine Rd")

    def test_format_person_json_multiple_address_fields_logs_warning(self):
        """Test that providing multiple address fields logs a warning"""
        from src.stac_utils.ngpvan import NGPVANClient

        with patch("src.stac_utils.ngpvan.logger") as mock_logger:
            result = NGPVANClient.format_person_json(
                {
                    "first_name": "John",
                    "last_name": "Smith",
                    "street_address": "123 Main St",
                    "address": "456 Other St",  # Duplicate - should trigger warning
                    "city": "Clinton",
                    "state": "IA",
                    "zip": "12345",
                },
                None,
                False,
            )
            mock_logger.warning.assert_called()
            # Should still use the first valid value found
            self.assertIn("addressLine1", result["addresses"][0])

    # =========================================================================
    # Address Parsing Tests
    # =========================================================================

    def test_format_person_json_address_parsing_full_address(self):
        """Test that full address is parsed when no city/state/zip provided"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "address": "123 Main St, Boston, MA 02101",
            },
            None,
            False,
        )
        self.assertIn("addresses", result)
        address = result["addresses"][0]
        # The parsed address should contain these components
        self.assertIn("addressLine1", address)
        self.assertIn("city", address)
        self.assertIn("stateOrProvince", address)
        self.assertIn("zipOrPostalCode", address)

    def test_format_person_json_address_not_parsed_when_city_present(self):
        """Test that address is not parsed when city is provided"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "address": "123 Main St, Boston, MA 02101",
                "city": "Springfield",  # City provided, so don't parse
            },
            None,
            False,
        )
        # Address should be used as-is, not parsed
        self.assertEqual(
            result["addresses"][0]["addressLine1"], "123 Main St, Boston, MA 02101"
        )
        self.assertEqual(result["addresses"][0]["city"], "Springfield")

    def test_format_person_json_address_not_parsed_when_state_present(self):
        """Test that address is not parsed when state is provided"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "address": "123 Main St, Boston, MA 02101",
                "state": "IL",
            },
            None,
            False,
        )
        self.assertEqual(
            result["addresses"][0]["addressLine1"], "123 Main St, Boston, MA 02101"
        )
        self.assertEqual(result["addresses"][0]["stateOrProvince"], "IL")

    def test_format_person_json_address_not_parsed_when_zip_present(self):
        """Test that address is not parsed when zip is provided"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "address": "123 Main St, Boston, MA 02101",
                "zip": "99999",
            },
            None,
            False,
        )
        self.assertEqual(
            result["addresses"][0]["addressLine1"], "123 Main St, Boston, MA 02101"
        )
        self.assertEqual(result["addresses"][0]["zipOrPostalCode"], "99999")

    # =========================================================================
    # Phone Field Alias and Comma-Delimited Tests
    # =========================================================================

    def test_format_person_json_phone_number_alias(self):
        """Test that 'phone_number' field is treated as phone"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "phone_number": "555-123-4567",
            },
            None,
            False,
        )
        self.assertEqual(result["phones"], [{"phoneNumber": "555-123-4567"}])

    def test_format_person_json_multiple_phones_comma_delimited(self):
        """Test that comma-delimited phones are parsed into multiple entries"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "phone": "555-111-1111, 555-222-2222, 555-333-3333",
            },
            None,
            False,
        )
        self.assertEqual(
            result["phones"],
            [
                {"phoneNumber": "555-111-1111"},
                {"phoneNumber": "555-222-2222"},
                {"phoneNumber": "555-333-3333"},
            ],
        )

    def test_format_person_json_multiple_phones_with_spaces(self):
        """Test that comma-delimited phones handle extra whitespace"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "phone": "  555-111-1111  ,   555-222-2222  ",
            },
            None,
            False,
        )
        self.assertEqual(
            result["phones"],
            [
                {"phoneNumber": "555-111-1111"},
                {"phoneNumber": "555-222-2222"},
            ],
        )

    def test_format_person_json_empty_phone_values_filtered(self):
        """Test that empty values in comma-delimited phones are filtered out"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "phone": "555-111-1111, , , 555-222-2222",
            },
            None,
            False,
        )
        self.assertEqual(
            result["phones"],
            [
                {"phoneNumber": "555-111-1111"},
                {"phoneNumber": "555-222-2222"},
            ],
        )

    # =========================================================================
    # Email Field Alias and Comma-Delimited Tests
    # =========================================================================

    def test_format_person_json_email_address_alias(self):
        """Test that 'email_address' field is treated as email"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "email_address": "john@example.com",
            },
            None,
            False,
        )
        self.assertEqual(result["emails"], [{"email": "john@example.com"}])

    def test_format_person_json_multiple_emails_comma_delimited(self):
        """Test that comma-delimited emails are parsed into multiple entries"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "email": "john@work.com, john@home.com, john@other.com",
            },
            None,
            False,
        )
        self.assertEqual(
            result["emails"],
            [
                {"email": "john@work.com"},
                {"email": "john@home.com"},
                {"email": "john@other.com"},
            ],
        )

    def test_format_person_json_multiple_emails_with_spaces(self):
        """Test that comma-delimited emails handle extra whitespace"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "email": "  john@work.com  ,   john@home.com  ",
            },
            None,
            False,
        )
        self.assertEqual(
            result["emails"],
            [
                {"email": "john@work.com"},
                {"email": "john@home.com"},
            ],
        )

    def test_format_person_json_empty_email_values_filtered(self):
        """Test that empty values in comma-delimited emails are filtered out"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "email": "john@work.com, , , john@home.com",
            },
            None,
            False,
        )
        self.assertEqual(
            result["emails"],
            [
                {"email": "john@work.com"},
                {"email": "john@home.com"},
            ],
        )

    # =========================================================================
    # Address Line 2 Tests
    # =========================================================================

    def test_format_person_json_address2(self):
        """Test that 'address2' field is treated as addressLine2"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "street_address": "123 Main St",
                "address2": "Apt 4B",
                "city": "Clinton",
                "state": "IA",
                "zip": "12345",
            },
            None,
            False,
        )
        self.assertEqual(result["addresses"][0]["addressLine2"], "Apt 4B")

    def test_format_person_json_address_2_alias(self):
        """Test that 'address_2' field is treated as addressLine2"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "street_address": "123 Main St",
                "address_2": "Suite 100",
                "city": "Clinton",
                "state": "IA",
                "zip": "12345",
            },
            None,
            False,
        )
        self.assertEqual(result["addresses"][0]["addressLine2"], "Suite 100")

    def test_format_person_json_street_address_2_alias(self):
        """Test that 'street_address_2' field is treated as addressLine2"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "street_address": "123 Main St",
                "street_address_2": "Floor 5",
                "city": "Clinton",
                "state": "IA",
                "zip": "12345",
            },
            None,
            False,
        )
        self.assertEqual(result["addresses"][0]["addressLine2"], "Floor 5")

    def test_format_person_json_address2_without_address1_logs_error(self):
        """Test that providing address2 without address1 logs an error"""
        from src.stac_utils.ngpvan import NGPVANClient

        with patch("src.stac_utils.ngpvan.logger") as mock_logger:
            result = NGPVANClient.format_person_json(
                {
                    "first_name": "John",
                    "last_name": "Smith",
                    "address_2": "Apt 4B",  # No address1 provided
                    "city": "Clinton",
                    "state": "IA",
                    "zip": "12345",
                },
                None,
                False,
            )
            mock_logger.error.assert_called()
            # addressLine2 should NOT be included when addressLine1 is missing
            self.assertNotIn("addressLine2", result["addresses"][0])

    # =========================================================================
    # Suffix Tests
    # =========================================================================

    def test_format_person_json_suffix(self):
        """Test that suffix field is included in output"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "suffix": "Jr.",
            },
            None,
            False,
        )
        self.assertEqual(result["suffix"], "Jr.")

    def test_format_person_json_suffix_various_values(self):
        """Test suffix with various common values"""
        from src.stac_utils.ngpvan import NGPVANClient

        for suffix in ["Jr.", "Sr.", "III", "IV", "PhD", "MD", "Esq."]:
            result = NGPVANClient.format_person_json(
                {
                    "first_name": "John",
                    "last_name": "Smith",
                    "suffix": suffix,
                },
                None,
                False,
            )
            self.assertEqual(result["suffix"], suffix)

    def test_format_person_json_no_suffix_when_empty(self):
        """Test that suffix is not included when empty or None"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "suffix": "",
            },
            None,
            False,
        )
        self.assertNotIn("suffix", result)

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "suffix": None,
            },
            None,
            False,
        )
        self.assertNotIn("suffix", result)

    # =========================================================================
    # Combined/Integration Tests
    # =========================================================================

    def test_format_person_json_all_new_features_combined(self):
        """Test using all new features together"""
        from src.stac_utils.ngpvan import NGPVANClient

        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "date_of_birth": "1984-01-01",
                "middle_name": "Jacob",
                "suffix": "Jr.",
                "email_address": "john@work.com, john@home.com",
                "phone_number": "555-111-1111, 555-222-2222",
                "address1": "123 Main St",
                "address_2": "Suite 500",
                "city": "Clinton",
                "state": "IA",
                "zip": "12345",
            },
            None,
            False,
        )

        self.assertEqual(result["firstName"], "John")
        self.assertEqual(result["lastName"], "Smith")
        self.assertEqual(result["middleName"], "Jacob")
        self.assertEqual(result["suffix"], "Jr.")
        self.assertEqual(
            result["emails"],
            [{"email": "john@work.com"}, {"email": "john@home.com"}],
        )
        self.assertEqual(
            result["phones"],
            [{"phoneNumber": "555-111-1111"}, {"phoneNumber": "555-222-2222"}],
        )
        self.assertEqual(
            result["addresses"],
            [
                {
                    "addressLine1": "123 Main St",
                    "addressLine2": "Suite 500",
                    "city": "Clinton",
                    "stateOrProvince": "IA",
                    "zipOrPostalCode": "12345",
                }
            ],
        )

    def test_format_person_json_backwards_compatibility(self):
        """Test that original functionality still works with original field names"""
        from src.stac_utils.ngpvan import NGPVANClient

        # This is essentially the same as the existing test, ensuring backwards compatibility
        result = NGPVANClient.format_person_json(
            {
                "first_name": "John",
                "last_name": "Smith",
                "date_of_birth": "1984-01-01",
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
        )

        self.assertEqual(result["firstName"], "John")
        self.assertEqual(result["lastName"], "Smith")
        self.assertEqual(result["emails"], [{"email": "foo@bar.com"}])
        self.assertEqual(result["phones"], [{"phoneNumber": "817-555-1234"}])
        self.assertEqual(result["addresses"][0]["addressLine1"], "123 Main")


    def test_validate_phone(self):
        self.test_client.post = MagicMock(return_value={"findbyphone": "555-123-4567"})
        self.assertEqual(
            "555-123-4567", self.test_client.validate_phone("555-123-4567")
        )

        self.test_client.post.assert_called_once_with(
            "people/findByPhone", body={"phoneNumber": "555-123-4567"}
        )

    def test_validate_phone_bad_phone(self):
        self.test_client.post = MagicMock(side_effect=NGPVANException)
        self.assertEqual("", self.test_client.validate_phone("555-123-4567"))


if __name__ == "__main__":
    unittest.main()
