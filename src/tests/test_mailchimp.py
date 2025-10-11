import os
import json
import unittest
import requests
from unittest.mock import patch, MagicMock, PropertyMock
from src.stac_utils.mailchimp import MailChimpClient, logger
from datetime import datetime, date


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

    @patch("src.stac_utils.mailchimp.time.sleep")
    # note the session is a property in the parent Client class, so can't use MagicMock
    @patch.object(MailChimpClient, "session", new_callable=PropertyMock)
    def test_request_with_retry_return_success(self, mock_session_property, mock_sleep):
        """Successful request should not delay in the loop"""
        mock_response = MagicMock(status_code=200)
        mock_session = MagicMock()
        mock_session.request.return_value = mock_response

        # property returns the mock session
        mock_session_property.return_value = mock_session

        response = self.test_client.request_with_retry(
            method="GET", endpoint_url="www.fake_endpoint.com/mail"
        )

        # client returns session object as given
        self.assertIs(response, mock_response)
        # request method called once
        mock_session.request.assert_called_once_with(
            method="GET", url="www.fake_endpoint.com/mail"
        )
        # retry not called
        mock_sleep.assert_not_called()

    @patch("src.stac_utils.mailchimp.time.sleep")
    # note the session is a property in the parent Client class, so can't use MagicMock
    @patch.object(MailChimpClient, "session", new_callable=PropertyMock)
    def test_request_with_retry_429_then_success(
        self, mock_session_property, mock_sleep
    ):
        """Should sleep and retry once after a 429 rate limit flag before succeeding"""

        # first response = 429
        mock_response_429 = MagicMock(status_code=429)
        # second response = 200
        mock_response_200 = MagicMock(status_code=200)

        # mock session that returns 429 once and then returns 200
        mock_session = MagicMock()
        mock_session.request.side_effect = [mock_response_429, mock_response_200]

        # MailChimpClient.session property returns mock session
        mock_session_property.return_value = mock_session

        # patching random.randint to return a set delay
        with patch(
            "src.stac_utils.mailchimp.random.randint", return_value=3
        ) as mock_rand:
            response = self.test_client.request_with_retry(
                method="GET", endpoint_url="www.fake_endpoint.com/mail"
            )

        # the function should return the 200 response
        self.assertIs(response, mock_response_200)

        # .request() method should have been called twice, first 429 then retried (200)
        self.assertEqual(mock_session.request.call_count, 2)

        # rand called once
        mock_rand.assert_called_once()

        # sleep called once with the set delay
        mock_sleep.assert_called_once_with(3)

    @patch("src.stac_utils.mailchimp.time.sleep")
    @patch.object(MailChimpClient, "session", new_callable=PropertyMock)
    def test_request_with_retry_hits_max_retries(
        self, mock_session_property, mock_sleep
    ):
        """Test that function retries max_retries times then returns the last 429 response"""
        # one mock per retry attempt
        mock_responses = [
            MagicMock(status_code=429) for _ in range(self.test_client.max_retries)
        ]
        mock_session = MagicMock()
        mock_session.request.side_effect = mock_responses
        mock_session_property.return_value = mock_session

        with patch("src.stac_utils.mailchimp.random.randint", return_value=3):
            response = self.test_client.request_with_retry(
                "GET", "www.fake_endpoint.com/mail"
            )
        # the final response should be the last of the mock_responses
        self.assertIs(response, mock_responses[-1])
        # times the mock object has been called should == the max_retries set
        self.assertEqual(mock_session.request.call_count, self.test_client.max_retries)
        # check to make sure number of delays == max_retries
        self.assertEqual(mock_sleep.call_count, self.test_client.max_retries)

    @patch("src.stac_utils.mailchimp.time.sleep")
    @patch.object(MailChimpClient, "session", new_callable=PropertyMock)
    def test_request_with_retry_handles_request_exception(
        self, mock_session_property, mock_sleep
    ):
        """Test when RequestException is raised before success"""
        # mock session
        mock_session = MagicMock()
        mock_response_200 = MagicMock(status_code=200)
        # first: raise exception
        # second: success
        mock_session.request.side_effect = [
            requests.exceptions.RequestException(),
            mock_response_200,
        ]
        mock_session_property.return_value = mock_session

        with patch("src.stac_utils.mailchimp.random.randint", return_value=3):
            response = self.test_client.request_with_retry(
                method="GET", endpoint_url="www.fake_endpoint.com/mail"
            )

        # final response should be success
        self.assertIs(response, mock_response_200)
        # function retries once after catching RequestException, and another ends in success
        self.assertEqual(mock_session.request.call_count, 2)
        # delay not called (only called if 429)
        mock_sleep.assert_not_called()

    @patch("src.stac_utils.mailchimp.time.sleep")
    @patch.object(MailChimpClient, "session", new_callable=PropertyMock)
    def test_request_with_retry_exception_when_complete_failure(
        self, mock_session_property, mock_sleep
    ):
        """Makes sure function raises RequestException when all retries fail with no response"""
        mock_session = MagicMock()
        # every call raises RequestException
        mock_session.request.side_effect = [
            requests.exceptions.RequestException(),
            requests.exceptions.RequestException(),
            requests.exceptions.RequestException(),
        ]
        mock_session_property.return_value = mock_session

        with patch("src.stac_utils.mailchimp.random.randint", return_value=3):
            # the final call will raise RequestException...
            with self.assertRaises(requests.exceptions.RequestException):
                self.test_client.request_with_retry(
                    method="GET", endpoint_url="www.fake_endpoint.com/mail"
                )

        # check to make sure number of retry attempts == max_retries
        self.assertEqual(mock_session.request.call_count, self.test_client.max_retries)
        # delay not called (only called if 429)
        mock_sleep.assert_not_called()

    @patch.object(MailChimpClient, "transform_response")
    @patch.object(logger, "debug")
    @patch.object(MailChimpClient, "request_with_retry")
    def test_paginate_endpoint_valid(
        self, mock_request_with_retry, mock_debug, mock_transform
    ):
        """Test that paginate_endpoint correctly aggregates results across multiple pages"""
        # set pages
        mock_transform.side_effect = [
            {"members": [{"id": "1"}, {"id": "2"}], "total_items": 4},
            {"members": [{"id": "3"}, {"id": "4"}], "total_items": 4},
        ]

        # set http calls
        fake_response_1 = MagicMock()
        fake_response_2 = MagicMock()
        mock_request_with_retry.side_effect = [fake_response_1, fake_response_2]

        results = self.test_client.paginate_endpoint(
            base_endpoint="lists/898/members",
            data_key="members",
            count=2,
            max_pages=2,
        )
        # all data in list
        self.assertEqual(results, [{"id": "1"}, {"id": "2"}, {"id": "3"}, {"id": "4"}])
        # two calls
        self.assertEqual(mock_request_with_retry.call_count, 2)
        # debug not called
        mock_debug.assert_not_called()

    @patch.object(MailChimpClient, "transform_response")
    @patch.object(logger, "debug")
    @patch.object(MailChimpClient, "request_with_retry")
    def test_paginate_endpoint_debug_logs_when_empty(
        self, mock_request_with_retry, mock_debug, mock_transform
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
        mock_request_with_retry.side_effect = [fake_response_1, fake_response_2]

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
        self.assertEqual(mock_request_with_retry.call_count, 2)

    @patch.object(MailChimpClient, "transform_response")
    @patch.object(logger, "debug")
    @patch.object(MailChimpClient, "request_with_retry")
    def test_paginate_endpoint_stops_when_total_items_reached(
        self, mock_request_with_retry, mock_debug, mock_transform
    ):
        """Test that paginate_endpoint stops paginating when offset >= total_items"""
        mock_transform.side_effect = [
            {"members": [{"id": "1"}, {"id": "2"}], "total_items": 3},
            {"members": [{"id": "3"}], "total_items": 3},
        ]

        # set HTTP calls
        fake_response_1 = MagicMock()
        fake_response_2 = MagicMock()
        mock_request_with_retry.side_effect = [fake_response_1, fake_response_2]

        results = self.test_client.paginate_endpoint(
            base_endpoint="lists/010/members",
            data_key="members",
            count=2,
        )

        # 3 total members
        self.assertEqual(results, [{"id": "1"}, {"id": "2"}, {"id": "3"}])
        # two calls
        self.assertEqual(mock_request_with_retry.call_count, 2)
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
    @patch.object(MailChimpClient, "request_with_retry")
    def test_update_member_tags_success_active(
        self, mock_request_with_retry, mock_transform
    ):
        """Test that update_member_tags correctly handles a 204 MailChimp success response for adding tags"""
        fake_response = MagicMock()
        fake_response.status_code = 204
        fake_response.content = b""
        mock_request_with_retry.return_value = fake_response

        mock_transform.return_value = {"status_code": 204}

        result = self.test_client.update_member_tags(
            list_id="102930al",
            email_address="fake@none.com",
            tags=["NEWS  ", "DONOR", " "],
            active=True,
        )

        expected_hash = self.test_client.get_subscriber_hash("fake@none.com")
        expected_url = f"https://us9.api.mailchimp.com/3.0/lists/102930al/members/{expected_hash}/tags"

        mock_request_with_retry.assert_called_once_with(
            method="POST",
            endpoint_url=expected_url,
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
    @patch.object(MailChimpClient, "request_with_retry")
    def test_update_member_tags_success_inactive(
        self, mock_request_with_retry, mock_transform
    ):
        """Test that update_member_tags correctly handles a 204 MailChimp success response for removing tags"""
        fake_response = MagicMock()
        fake_response.status_code = 204
        fake_response.content = b""
        mock_request_with_retry.return_value = fake_response

        mock_transform.return_value = {"status_code": 204}

        result = self.test_client.update_member_tags(
            list_id="102930al",
            email_address="fake@none.com",
            tags=["NEWS  ", "DONOR", " "],
            active=False,
        )

        expected_hash = self.test_client.get_subscriber_hash("fake@none.com")
        expected_url = f"https://us9.api.mailchimp.com/3.0/lists/102930al/members/{expected_hash}/tags"

        mock_request_with_retry.assert_called_once_with(
            method="POST",
            endpoint_url=expected_url,
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

    @patch.object(logger, "info")
    @patch.object(MailChimpClient, "request_with_retry")
    def test_update_member_tags_empty_tag_payload(
        self, mock_request_with_retry, mock_info
    ):
        """Test that update_member_tags returns early when no valid tags exist"""
        # no good tags in the payload
        result = self.test_client.update_member_tags(
            list_id="102930al",
            email_address="fake@none.com",
            tags=["   ", "", None],
            active=True,
        )

        # check the return
        self.assertEqual(result, {"status_code": 204, "info": "No valid tags provided"})

        # no retries
        mock_request_with_retry.assert_not_called()

        # check the log message
        mock_info.assert_called_once_with(
            "No valid tags provided for email: fake@none.com"
        )

    @patch.object(MailChimpClient, "transform_response")
    @patch.object(MailChimpClient, "format_merge_fields_for_list")
    @patch.object(MailChimpClient, "request_with_retry")
    def test_upsert_member_success(
        self, mock_request_with_retry, mock_format, mock_transform
    ):
        """Test that upsert_member sends correct payload and handles MailChimp 200 JSON response"""

        fake_response = MagicMock()
        fake_response.status_code = 200

        mock_request_with_retry.return_value = fake_response
        mock_transform.return_value = {
            "id": "8121stac",
            "email_address": "fake@none.com",
            "status_code": 200,
        }

        mock_format.return_value = {"FNAME": "Fake", "LNAME": "Dude"}

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
        mock_request_with_retry.assert_called_once_with(
            method="PUT", endpoint_url=expected_url, json=expected_payload
        )
        # return is called once
        mock_transform.assert_called_once_with(fake_response)
        # format_merge_fields_for_list called once
        mock_format.assert_called_once_with(list_id, merge_fields)
        # success
        self.assertEqual(result["status_code"], 200)
        # compare final email val to expected
        self.assertEqual(result["email_address"], "fake@none.com")

    @patch.object(MailChimpClient, "transform_response")
    @patch.object(MailChimpClient, "request_with_retry")
    def test_upsert_member_fail(self, mock_request_with_retry, mock_transform):
        """Test that upsert_member raises error when merge fields contain fake tags"""
        list_id = "102930al"
        email_address = "fake@none.com"

        # have to include this, as otherwise tests will fail as no datatype mapping
        with patch.object(
            MailChimpClient,
            "get_merge_fields_data_type_map",
            return_value={"FNAME": "text"},
        ):
            # test KeyError is raised
            with self.assertRaises(KeyError):
                self.test_client.upsert_member(
                    list_id=list_id,
                    email_address=email_address,
                    merge_fields={"FAKE_MERGE_TAG": "some_val"},
                )

        # no put call for upsert should have occurred
        mock_request_with_retry.assert_not_called()
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
    def test_format_merge_fields_for_list_zip_success(self, mock_get_types):
        """Test that zip with exactly 5 digits succeeds"""
        mock_get_types.return_value = {"ZIP": "zip"}

        merge_fields = {"ZIP": "11111"}

        result = self.test_client.format_merge_fields_for_list("oapao1", merge_fields)

        mock_get_types.assert_called_once_with("oapao1")
        self.assertEqual(result, {"ZIP": "11111"})

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

    def test_format_date(self):
        """Test where input value is a date/datetime or string instance"""
        # using datetime
        datetime_value = datetime(2025, 1, 1)
        function_datetime = self.test_client.format_date(datetime_value)
        self.assertEqual(function_datetime, "2025-01-01")

        # using date
        date_value = date(2025, 1, 1)
        function_date = self.test_client.format_date(date_value)
        self.assertEqual(function_date, "2025-01-01")

        # using string
        function_string = self.test_client.format_date(" 2025-01-01   ")
        self.assertEqual(function_string, "2025-01-01")

        # covers some other string formatted cases
        self.assertEqual(self.test_client.format_date("01/01/2025"), "2025-01-01")
        self.assertEqual(self.test_client.format_date("01-01-2025"), "2025-01-01")

        # ValueError raised when not a date
        with self.assertRaises(ValueError):
            self.test_client.format_date("not a date, obviously")

    def test_format_birthday(self):
        """Test where input value is a date/datetime or string instance"""
        # using datetime
        datetime_value = datetime(2025, 1, 1)
        function_datetime = self.test_client.format_birthday(datetime_value)
        self.assertEqual(function_datetime, "01/01")

        # using date
        date_value = date(2025, 1, 1)
        function_date = self.test_client.format_birthday(date_value)
        self.assertEqual(function_date, "01/01")

        # using string
        function_string = self.test_client.format_birthday(" 01/01 ")
        self.assertEqual(function_string, "01/01")

        # covers some other string formatted cases
        self.assertEqual(self.test_client.format_birthday("01-01"), "01/01")
        self.assertEqual(self.test_client.format_birthday("2025-01-01"), "01/01")
        self.assertEqual(self.test_client.format_birthday("2025/01/01"), "01/01")

        # ValueError raised when not a date
        with self.assertRaises(ValueError):
            self.test_client.format_birthday("not a date, obviously")

    def test_format_address(self):
        """Test format_address returns the correct values"""
        # when input val is not a dict
        with self.assertRaises(ValueError):
            self.test_client.format_address("not a dict, obviously")

        # create a dict to test the normalize_string function nested in format_address
        function_address_valid = self.test_client.format_address(
            {
                "addr1": "999 Dolly Ave",
                "addr2": " Apt 3   ",
                "city": "Delaware",
                "state": "PA",
                "zip": 90210,
                "country": "USA ",
            }
        )

        # check if one req element exists
        self.assertIn("addr1", function_address_valid)
        # check formatted val of addr1
        self.assertEqual(function_address_valid["addr1"], "999 Dolly Ave")
        # check that a numeric val is now string
        self.assertEqual(function_address_valid["zip"], "90210")
        # coverage on the string trimming
        self.assertEqual(function_address_valid["addr2"], "Apt 3")

        # creating an invalid req
        with self.assertRaises(ValueError):
            self.test_client.format_address({"addr2": "999 Dolly Ave "})
