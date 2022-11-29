import unittest

from src.stac_utils.http import Client, HTTPClient


class TestClient(unittest.TestCase):
    def test_init(self):
        """ Test init raises type error because it's an abstract class """

        self.assertRaises(TypeError, Client())


class TestHTTPClient(unittest.TestCase):
    def test_init(self):
        """ Test init"""

    def test_rate_limits(self):
        """ Test rate limits """

    def test_wait_for_rate(self):
        """ Test wait for rate limits """

    def test_check_response_for_rate_limit(self):
        """ Test check response for rate limit """

    def test_format_url(self):
        """ Test format url """

    def test_call_api(self):
        """ Test call api """

    def test_call_api_with_404(self):
        """ Test call api with 404 exception """

    def test_call_api_with_401(self):
        """ Test call api with hitting rate limit """

    def test_call_api_with_429(self):
        """ Test call api with expired auth """

    def test_call_api_with_connection_error(self):
        """ Test call api with status code free connection error """

    def test_get(self):
        """ Test GET """

    def test_post(self):
        """ Test POST """

    def test_put(self):
        """ Test PUT """

    def test_patch(self):
        """ Test PATCH """

    def test_delete(self):
        """ Test DELETE """

    def test_update_rate_limits(self):
        """ Test update rate limits """

    def test_create_session(self):
        """ Test create session """

    def test_refresh_auth(self):
        """ test refresh auth """

    def test_clean_up(self):
        """ Test clean up """


if __name__ == '__main__':
    unittest.main()
