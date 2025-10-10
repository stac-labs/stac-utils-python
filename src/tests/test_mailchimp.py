import os
import json
import unittest
from unittest.mock import patch, MagicMock
from src.stac_utils.mailchimp import MailChimpClient, logger


class TestMailChimpClient(unittest.TestCase):
    def setUp(self) -> None:
        self.test_client = MailChimpClient(api_key="fake-us9")
        self.test_logger = logger

    def test_init_env_keys(self):
        """Test that client initializes with environmental keys"""
        test_api_key = "hgd1204-us20"
        with patch.dict(os.environ, values={"MAILCHIMP_API_KEY": test_api_key}):
            test_client = MailChimpClient()
            self.assertEqual(test_api_key, test_client.api_key)
            # test the extracted data center and base_url
            self.assertEqual("us20", test_client.data_center)
            self.assertEqual("https://us20.api.mailchimp.com/3.0", test_client.base_url)

    def test_create_session(self):
        """Test that API token and content type is set in headers for a Mailchimp session"""
        session = self.test_client.create_session()

        # check that the auth tuple is correctly set
        self.assertEqual(session.auth, ("anystring", self.test_client.api_key))

        # check that the "Content-Type" header exists and has a value of "application/json"
        self.assertIn("Content-Type", session.headers)
        self.assertEqual(session.headers["Content-Type"], "application/json")

    def test_transform_response_valid_json(self):
        """Test that response is transformed and includes status code"""
        mock_data = {"foo_bar": "spam", "email_address": "fake@none.com"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        # http response body contains bytes
        mock_response.content = json.dumps(mock_data).encode()
        mock_response.json.return_value = mock_data
        result = self.test_client.transform_response(mock_response)
        # make sure output matches expected dict
        self.assertEqual(
            result,
            {"foo_bar": "spam", "email_address": "fake@none.com", "status_code": 200},
        )

    def test_transform_response_empty_content(self):
        """Test that empty content or a 204 response returns only the status code"""
        mock_response = MagicMock()
        mock_response.status_code = 204
        # no data returned in 204 response
        mock_response.content = b""
        result = self.test_client.transform_response(mock_response)
        self.assertEqual(result, {"status_code": 204})

    def test_transform_response_invalid_json(self):
        """Test that response for invalid JSON returns an empty dict with the status code"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.content = b"not a valid json"
        # bad json
        mock_response.json.side_effect = json.decoder.JSONDecodeError(
            "error", "not a valid json", 0
        )
        result = self.test_client.transform_response(mock_response)
        self.assertEqual(result, {"status_code": 500})

    @patch.object(logger, "warning")
    def test_check_response_for_rate_limit(self, mock_warning):
        """Test that check_response_for_rate_limit always returns 1 and actually logs warning on 429"""
        mock_response_valid = MagicMock()
        mock_response_valid.status_code = 200

        mock_response_limit = MagicMock()
        mock_response_limit.status_code = 429

        # should always return 1
        result_valid = self.test_client.check_response_for_rate_limit(
            mock_response_valid
        )
        result_limit = self.test_client.check_response_for_rate_limit(
            mock_response_limit
        )

        self.assertEqual(result_valid, 1)
        self.assertEqual(result_limit, 1)

        # verify that the logger warning called once (occurs when 429)
        mock_warning.assert_called_once_with(
            "Mailchimp rate limit hit (HTTP 429: Too Many Requests)"
        )

    @patch.object(MailChimpClient, "transform_response")
    @patch.object(logger, "debug")
    @patch("requests.Session.get")
    def test_paginate_endpoint_valid(self, mock_get, mock_debug, mock_transform):
        """Test that paginate_endpoint correctly aggregates results across multiple pages"""
        # set pages
        mock_transform.side_effect = [
            {"members": [{"id": "1"}, {"id": "2"}], "total_items": 4},
            {"members": [{"id": "3"}, {"id": "4"}], "total_items": 4},
        ]

        # set http calls
        fake_response_1 = MagicMock()
        fake_response_2 = MagicMock()
        mock_get.side_effect = [fake_response_1, fake_response_2]

        results = self.test_client.paginate_endpoint(
            base_endpoint="lists/898/members",
            data_key="members",
            count=2,
            max_pages=2,
        )
        # all data in list
        self.assertEqual(results, [{"id": "1"}, {"id": "2"}, {"id": "3"}, {"id": "4"}])
        # two calls
        self.assertEqual(mock_get.call_count, 2)
        # debug not called
        mock_debug.assert_not_called()

    @patch.object(MailChimpClient, "transform_response")
    @patch.object(logger, "debug")
    @patch("requests.Session.get")
    def test_paginate_endpoint_debug_logs_when_empty(
        self, mock_get, mock_debug, mock_transform
    ):
        """Test that paginate_endpoint logs debug message and stops when no items are found"""
        # mock first page has data, second page empty (triggers debug...)
        mock_transform.side_effect = [
            {"members": [{"id": "1"}, {"id": "2"}], "total_items": 4},
            {"members": []},
        ]

        # set HTTP calls
        fake_response_1 = MagicMock()
        fake_response_2 = MagicMock()
        mock_get.side_effect = [fake_response_1, fake_response_2]

        self.test_client.paginate_endpoint(
            base_endpoint="lists/898/members",
            data_key="members",
            count=2,
        )

        # should log debug once when second page is empty
        mock_debug.assert_called_once_with(
            "No items found at offset 2 for key 'members'"
        )
        # two calls
        self.assertEqual(mock_get.call_count, 2)

    @patch.object(MailChimpClient, "transform_response")
    @patch.object(logger, "debug")
    @patch("requests.Session.get")
    def test_paginate_endpoint_stops_when_total_items_reached(
        self, mock_get, mock_debug, mock_transform
    ):
        """Test that paginate_endpoint stops paginating when offset >= total_items"""
        mock_transform.side_effect = [
            {"members": [{"id": "1"}, {"id": "2"}], "total_items": 3},
            {"members": [{"id": "3"}], "total_items": 3},
        ]

        # set HTTP calls
        fake_response_1 = MagicMock()
        fake_response_2 = MagicMock()
        mock_get.side_effect = [fake_response_1, fake_response_2]

        results = self.test_client.paginate_endpoint(
            base_endpoint="lists/010/members",
            data_key="members",
            count=2,
        )

        # 3 total members
        self.assertEqual(results, [{"id": "1"}, {"id": "2"}, {"id": "3"}])
        # two calls
        self.assertEqual(mock_get.call_count, 2)
        # debug not called
        mock_debug.assert_not_called()

    def test_get_subscriber_hash(self):
        """Test that get_subscriber_hash returns correct md5 hash and normalizes to lowercase"""
        email = "wEiRd@staclabs.coM"
        expected_subscriber_hash = "67441e845c03ceda61635c3263393515"

        result = MailChimpClient.get_subscriber_hash(email)
        self.assertEqual(result, expected_subscriber_hash)

        # lowercase version
        self.assertEqual(
            result, MailChimpClient.get_subscriber_hash("weird@staclabs.com")
        )

    @patch.object(MailChimpClient, "transform_response")
    @patch("requests.Session.post")
    def test_update_member_tags_success_active(self, mock_post, mock_transform):
        """Test that update_member_tags correctly handles a 204 MailChimp success response for adding tags"""
        fake_response = MagicMock()
        fake_response.status_code = 204
        fake_response.content = b""
        mock_post.return_value = fake_response

        mock_transform.return_value = {"status_code": 204}

        result = self.test_client.update_member_tags(
            list_id="102930al",
            email_address="fake@none.com",
            tags=["NEWS  ", "DONOR", " "],
            active=True,
        )

        expected_hash = self.test_client.get_subscriber_hash("fake@none.com")
        expected_url = f"https://us9.api.mailchimp.com/3.0/lists/102930al/members/{expected_hash}/tags"

        mock_post.assert_called_once_with(
            expected_url,
            json={
                "tags": [
                    {"name": "NEWS", "status": "active"},
                    {"name": "DONOR", "status": "active"},
                ]
            },
        )

        # transform_response called once
        mock_transform.assert_called_once_with(fake_response)

        # no body in this call, just the status code
        self.assertEqual(result, {"status_code": 204})

    @patch.object(MailChimpClient, "transform_response")
    @patch("requests.Session.post")
    def test_update_member_tags_success_inactive(self, mock_post, mock_transform):
        """Test that update_member_tags correctly handles a 204 MailChimp success response for removing tags"""
        fake_response = MagicMock()
        fake_response.status_code = 204
        fake_response.content = b""
        mock_post.return_value = fake_response

        mock_transform.return_value = {"status_code": 204}

        result = self.test_client.update_member_tags(
            list_id="102930al",
            email_address="fake@none.com",
            tags=["NEWS  ", "DONOR", " "],
            active=False,
        )

        expected_hash = self.test_client.get_subscriber_hash("fake@none.com")
        expected_url = f"https://us9.api.mailchimp.com/3.0/lists/102930al/members/{expected_hash}/tags"

        mock_post.assert_called_once_with(
            expected_url,
            json={
                "tags": [
                    {"name": "NEWS", "status": "inactive"},
                    {"name": "DONOR", "status": "inactive"},
                ]
            },
        )

        # transform_response called once
        mock_transform.assert_called_once_with(fake_response)

        # no body in this call, just the status code
        self.assertEqual(result, {"status_code": 204})

    # have to include this, as otherwise tests will fail as no datatype mapping
    @patch.object(
        MailChimpClient,
        "get_merge_fields_data_type_map",
        return_value={"FNAME": "text", "LNAME": "text"},
    )
    @patch.object(MailChimpClient, "transform_response")
    @patch("requests.Session.put")
    def test_upsert_member_success(
        self, mock_put, mock_transform, mock_merge_fields_map
    ):
        """Test that upsert_member sends correct payload and handles MailChimp 200 JSON response"""

        fake_response = MagicMock()
        fake_response.status_code = 200

        mock_put.return_value = fake_response
        mock_transform.return_value = {
            "id": "8121stac",
            "email_address": "fake@none.com",
            "status_code": 200,
        }

        list_id = "102930al"
        email_address = "fake@none.com"
        merge_fields = {"FNAME": "Fake", "LNAME": "Dude"}

        result = self.test_client.upsert_member(
            list_id=list_id, email_address=email_address, merge_fields=merge_fields
        )

        expected_hash = self.test_client.get_subscriber_hash(email_address)
        expected_url = (
            f"https://us9.api.mailchimp.com/3.0/lists/{list_id}/members/{expected_hash}"
        )

        expected_payload = {
            "email_address": email_address,
            "status_if_new": "subscribed",
            "merge_fields": merge_fields,
        }
        # put called once
        mock_put.assert_called_once_with(expected_url, json=expected_payload)
        # return is called once
        mock_transform.assert_called_once_with(fake_response)
        # success
        self.assertEqual(result["status_code"], 200)
        # compare final email val to expected
        self.assertEqual(result["email_address"], "fake@none.com")

    # have to include this, as otherwise tests will fail as no datatype mapping
    @patch.object(
        MailChimpClient,
        "get_merge_fields_data_type_map",
        return_value={"FNAME": "text"},
    )
    @patch.object(MailChimpClient, "transform_response")
    @patch("requests.Session.put")
    def test_upsert_member_fail(self, mock_put, mock_transform, mock_merge_fields_map):
        """Test that upsert_member raises error when merge fields contain fake tags"""
        list_id = "102930al"
        email_address = "fake@none.com"

        # test KeyError is raised
        with self.assertRaises(KeyError):
            self.test_client.upsert_member(
                list_id=list_id,
                email_address=email_address,
                merge_fields={"FAKE_MERGE_TAG": "some_val"},
            )

        # no put call for upsert should have occurred
        mock_put.assert_not_called()
        # no transform_response call for upsert should have occurred
        mock_transform.assert_not_called()

    @patch.object(MailChimpClient, "paginate_endpoint")
    def test_get_merge_fields_data_type_map_success(self, mock_paginate):
        """Test that get_merge_fields_data_type_map returns correct mapping on success"""
        mock_paginate.return_value = [
            {"tag": "FNAME", "type": "text"},
            {"tag": "LNAME", "type": "text"},
            {"tag": "VAN_ID", "type": "number"},
        ]

        list_id = "98798798h"

        result = self.test_client.get_merge_fields_data_type_map(list_id)

        mock_paginate.assert_called_once_with(
            base_endpoint=f"lists/{list_id}/merge-fields", data_key="merge_fields"
        )

        expected_map = {"FNAME": "text", "LNAME": "text", "VAN_ID": "number"}
        self.assertEqual(result, expected_map)

    @patch.object(MailChimpClient, "paginate_endpoint")
    def test_get_merge_fields_data_type_map_fail(self, mock_paginate):
        """Test that get_merge_fields_data_type_map returns empty dict fail"""

        # paginate_endpoint returns no data
        mock_paginate.return_value = [{}]

        list_id = "zzzz"
        result = self.test_client.get_merge_fields_data_type_map(list_id)

        # paginate_endpoint called once
        mock_paginate.assert_called_once_with(
            base_endpoint=f"lists/{list_id}/merge-fields", data_key="merge_fields"
        )

        # empty dict for result
        self.assertEqual(result, {})

    @patch.object(MailChimpClient, "get_merge_fields_data_type_map")
    def test_format_merge_fields_for_list_skips_blank_and_none(self, mock_get_types):
        """Test that None and blank strings are ignored"""
        mock_get_types.return_value = {"FNAME": "text", "LNAME": "text"}

        merge_fields = {"FNAME": None, "LNAME": " "}
        result = self.test_client.format_merge_fields_for_list("llll", merge_fields)
        # should be an empty dict
        self.assertEqual(result, {})

    @patch.object(MailChimpClient, "get_merge_fields_data_type_map")
    def test_format_merge_fields_for_list_text_success(self, mock_get_types):
        """Test that text fields are handled correctly."""
        mock_get_types.return_value = {"FNAME": "text", "LNAME": "text"}

        merge_fields = {"FNAME": "  John  ", "LNAME": "Doe"}
        result = self.test_client.format_merge_fields_for_list("oapao1", merge_fields)

        mock_get_types.assert_called_once_with("oapao1")
        self.assertEqual(result, {"FNAME": "John", "LNAME": "Doe"})

    @patch.object(MailChimpClient, "get_merge_fields_data_type_map")
    def test_format_merge_fields_for_list_zip_fail(self, mock_get_types):
        """Test that zip type over 5 digits raise error"""
        mock_get_types.return_value = {"ZIP": "zip"}

        merge_fields = {"ZIP": "1111122"}

        with self.assertRaises(ValueError):
            self.test_client.format_merge_fields_for_list("some_id", merge_fields)

    @patch.object(MailChimpClient, "get_merge_fields_data_type_map")
    def test_format_merge_fields_for_list_with_helpers(self, mock_get_types):
        """Test that date, birthday, address, and number fields are pushed to the correct helper function"""
        mock_get_types.return_value = {
            "DATE": "date",
            "BIRTHDAY": "birthday",
            "ADDRESS": "address",
            "NUMBER": "number",
        }

        # replace methods with mocks
        with patch.object(self.test_client, "format_date") as mock_date, patch.object(
            self.test_client, "format_birthday"
        ) as mock_bday, patch.object(
            self.test_client,
            "format_address",
        ) as mock_addr, patch.object(
            self.test_client,
            "format_number",
        ) as mock_num:
            # placeholder fake data
            merge_fields = {
                "DATE": "2022-10-09",
                "BIRTHDAY": "10/09",
                "ADDRESS": {},
                "NUMBER": 0,
            }

            self.test_client.format_merge_fields_for_list("some_id", merge_fields)
            # just test if helper methods were called
            mock_date.assert_called_once()
            mock_bday.assert_called_once()
            mock_addr.assert_called_once()
            mock_num.assert_called_once()
