import unittest

from src.stac_utils.ticker_request import TickerRequest


class TestTickerRequest(unittest.TestCase):
    def test_init(self):
        """Test init"""

    def test_init_no_auth(self):
        """Test init with missing auth"""

    def test_create_session(self):
        """Test create session"""

    def test_transform_response(self):
        """Test transform response"""

    def test_check_for_error_when_exists(self):
        """Test check for error when one exists"""

    def test_check_for_error_when_not_exists(self):
        """Test check for error when one does not exist"""

    def test_add_data(self):
        """Test add data"""

    def test_send_to_ticker(self):
        """Test send to ticker"""

    def test_send_to_ticker_no_data(self):
        """Test send to ticker with no data"""

    def test_send_to_ticker_with_error(self):
        """Test send to ticker when error happens"""


if __name__ == "__main__":
    unittest.main()
