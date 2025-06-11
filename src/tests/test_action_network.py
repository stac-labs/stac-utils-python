import os
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from src.stac_utils.action_network import ActionNetworkClient, logger


class TestActionNetworkClient(unittest.TestCase):
    def setUp(self) -> None:
        self.test_client = ActionNetworkClient()
        self.test_logger = logger

    def test_init_env_keys(self):
        """Test that client initializes with environmental keys"""
        test_api_token = "foo"

        with patch.dict(os.environ, values={"ACTIONNETWORK_API_TOKEN": test_api_token}):
            test_client = ActionNetworkClient()
            self.assertEqual(test_api_token, test_client.api_token)

    def test_create_session(self):
        """Make sure API token and content type set in headers"""
        test_client = ActionNetworkClient("foo")
        self.assertTrue(
            {
                "OSDI-API-Token": test_client.api_token,
                "Content-Type": "application/json",
            }.items()
            <= test_client.session.headers.items(),
        )

    def test_transform_response(self):
        """Test that response is transformed and includes status code"""
        mock_data = {"foo_bar": "spam"}
        mock_response = MagicMock()
        mock_response.status_code = 42
        mock_response.json = MagicMock(return_value=mock_data)

        test_data = self.test_client.transform_response(mock_response)
        self.assertEqual({"foo_bar": "spam", "status_code": 42}, test_data)

    def test_check_response_for_rate_limit(self):
        """Test that response has rate limit of 1"""
        test_client = ActionNetworkClient("foo")
        self.assertEqual(1, test_client.check_response_for_rate_limit(None))

    def test_extract_action_network_id_valid(self):
        """Test that the correct Action Network ID is extracted"""
        identifiers = ["not_an:123aabb", "action_network:foo12bar", "random_id:120930a"]
        output = self.test_client.extract_action_network_id(identifiers)
        self.assertEqual(output, "foo12bar")

    def test_extract_action_network_id_empty(self):
        """test for empty string when no Action Network ID"""
        identifiers = ["not_an:123aabb", "random_id:120930a"]
        output = self.test_client.extract_action_network_id(identifiers)
        self.assertEqual(output, "")

    def test_create_people_dataframe(self):
        """Test that create_people_dataframe function correctly extracts/maps all fields from person record into
        the resultant DataFrame."""
        people_data = [
            {
                "identifiers": ["action_network:askjdaskdjfh12", "spam:fo1212o"],
                "given_name": "fake_first_name",
                "family_name": "fake_last_name",
                "email_addresses": [{"address": "fake@example.com"}],
                "phone_numbers": [{"number": "999-999-9999"}],
                "postal_addresses": [
                    {
                        "postal_code": "90210-1234",
                        "address_lines": ["999 Fake Street"],
                        "locality": "Beverly Hills",
                        "region": "CA",
                    }
                ],
            }
        ]

        expected_df = pd.DataFrame(
            [
                {
                    "action_network_id": "askjdaskdjfh12",
                    "first_name": "fake_first_name",
                    "last_name": "fake_last_name",
                    "email_address": "fake@example.com",
                    "phone": "999-999-9999",
                    "zip5": "90210",
                    "street_name": "999 Fake Street",
                    "city": "Beverly Hills",
                    "state": "CA",
                }
            ]
        )

        result_df = self.test_client.create_people_dataframe(people_data)
        # preserve column/row order when comparing dfs
        self.assertEqual(
            expected_df.to_dict(orient="records"), result_df.to_dict(orient="records")
        )

    @patch.object(ActionNetworkClient, "get")
    def test_paginate_endpoint_valid(self, mock_get):
        """
        Test to see if the paginate_endpoint function gathers results across multiple pages using the embedded_key
        param.
        """
        # check paginated API responses
        mock_get.side_effect = [
            {"_embedded": {"osdi:forms": [{"val": 1}, {"val": 2}]}},
            {"_embedded": {"osdi:forms": [{"val": 3}]}},
            {"_embedded": {"osdi:forms": [{"val": 4}]}},
        ]

        # checks if the results properly grab only first 2 pages of results, based on mock calls
        results = self.test_client.paginate_endpoint(
            "forms", embedded_key="osdi:forms", max_pages=2
        )
        self.assertEqual(results, [{"val": 1}, {"val": 2}, {"val": 3}])
        self.assertEqual(mock_get.call_count, 2)

    @patch.object(logger, "debug")
    @patch.object(ActionNetworkClient, "get")
    def test_paginate_endpoint_empty(self, mock_get, mock_debug):
        """
        check for logger debug message when the next page's _embedded list is empty
        """
        mock_get.side_effect = [
            {"_embedded": {"osdi:forms": [{"val": 1}, {"val": 2}]}},
            {"_embedded": {"osdi:forms": [{"val": 3}]}},
            {"_embedded": {"osdi:forms": []}},
        ]
        self.test_client.paginate_endpoint("forms", embedded_key="osdi:forms")
        mock_debug.assert_called_with("No items found at page 3 for key 'osdi:forms'")

    @patch.object(ActionNetworkClient, "get")
    def test_fetch_related_people_valid(self, mock_get):
        """
        Tests if the fetch_related_people correctly fetches and returns related people records
        """
        # fake data for GET calls (not all data in a person dict, but doesnt matter for testing)
        person_1 = {
            "identifiers": ["action_network:12ab234"],
            "given_name": "Fake",
            "family_name": "Name",
        }

        person_2 = {
            "identifiers": ["action_network:182awe"],
            "given_name": "Mock",
            "family_name": "Test",
        }

        # setup mock_get to return these person dicts in order
        mock_get.side_effect = [person_1, person_2]

        # build resoruce, including two keys for fun to test
        resource = {
            "_links": {
                "osdi:person": {
                    "href": "https://actionnetwork.org/api/v2/people/12ab234"
                },
                "osdi:guest_person": {
                    "href": "https://actionnetwork.org/api/v2/people/182awe"
                },
            }
        }

        # get output of function
        people = self.test_client.fetch_related_people(
            resource, person_link_keys=["osdi:person", "osdi:guest_person"]
        )

        # check for GET request
        mock_get.assert_any_call("people/12ab234")
        mock_get.assert_any_call("people/182awe")

        # check that the output matches the mocked responses
        self.assertEqual(people, [person_1, person_2])

    @patch.object(ActionNetworkClient, "get")
    def test_fetch_related_people_default_key(self, mock_get):
        """
        Tests if person_link_keys defaults to ["osdi:person"]
        """
        # fake data for GET calls (not all data in a person dict, but doesnt matter for testing)
        person_1 = {
            "identifiers": ["action_network:12ab234"],
            "given_name": "Fake",
            "family_name": "Name",
        }

        # setup mock_get to return these person dicts in order
        mock_get.side_effect = [person_1]

        # build resoruce, including two keys for fun to test
        resource = {
            "_links": {
                "osdi:person": {
                    "href": "https://actionnetwork.org/api/v2/people/12ab234"
                },
            }
        }

        # get output of function, using default key
        people = self.test_client.fetch_related_people(resource)

        # check for GET request
        mock_get.assert_any_call("people/12ab234")

        # check that the output matches the mocked responses
        self.assertEqual(people, [person_1])

    @patch.object(ActionNetworkClient, "get")
    def test_fetch_related_people_link_info_none(self, mock_get):
        """Test that fetch_related_people skips if link_info is None."""
        resource = {
            "_links": {
                "osdi:person": None,
            }
        }
        people = self.test_client.fetch_related_people(
            resource, person_link_keys=["osdi:person"]
        )
        self.assertEqual(people, [])
        mock_get.assert_not_called()

    @patch.object(ActionNetworkClient, "get")
    def test_fetch_related_people_href_empty_or_missing_correct_endpoint(self, mock_get):
        """Test that fetch_related_people skips if href key is missing or doesn't contain 'people/'."""
        resource = {
            "_links": {
                "osdi:person": {"href": None},
                "osdi:guest_person": {
                    "href": "https://actionnetwork.org/api/v2/superfake/spam"
                },
            }
        }
        people = self.test_client.fetch_related_people(
            resource, person_link_keys=["osdi:person", "osdi:guest_person"]
        )
        self.assertEqual(people, [])
        mock_get.assert_not_called()
