import unittest

from src.stac_utils.ngpvan import NGPVANClient, NGPVANException, NGPVANLocationException


class TestNGPVAN(unittest.TestCase):
    def test_init(self):
        """ Test that client intiates """

    def test_init_env_keys(self):
        """ Test keys are pulled from env if not present """

    def test_create_session(self):
        """ Test session has api keys """

    def test_check_response_for_rate_limit(self):
        """ Test that it returns 2 """

    def test_transform_response(self):
        """ Test transform response handles normal data """

    def test_transform_response_headers(self):
        """ Test transform response returns headers """

    def test_transform_response_snake_case(self):
        """ Test transform response transforms key names into snake case """

    def test_transform_response_request_exception(self):
        """ Test transform response handles exception in the response """

    def test_transform_response_json_decoder_error(self):
        """ Test transform response handles bad json data """

    def test_transform_response_other_exception(self):
        """ Test transform response handles something else going wrong """

    def test_check_for_error(self):
        """ Test check for error finds no error when no error is present """

    def test_check_for_error_with_errors(self):
        """ Test check for error finds an non-location error when included """

    def test_check_for_error_with_location_errors(self):
        """ Test check for error finds a location error """

    def test_get_paginated_items(self):
        """ Test it pages through multiple urls """

    def test_get_paginated_items_one_page(self):
        """ Test it pages through one page """


if __name__ == '__main__':
    unittest.main()
