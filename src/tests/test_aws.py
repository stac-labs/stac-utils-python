import unittest

from src.stac_utils.aws import get_secret, write_secret, load_from_s3, save_to_s3


class TestAWS(unittest.TestCase):
    def test_get_secret(self):
        """Test get secret"""

    def test_get_secret_does_not_exist(self):
        """Test get secret when it doesn't exist"""

    def test_write_secret(self):
        """Test write secret"""

    def test_write_secret_does_not_exist(self):
        """Test write secret when it doesn't exist"""

    def test_load_from_s3(self):
        """Test load from s3"""

    def test_load_from_s3_expired_token(self):
        """Test load from s3 with expired token"""

    def test_load_from_s3_client_error(self):
        """Test load from s3 with client error"""

    def test_load_from_s3_json_decoder_error(self):
        """Test load from s3 with bad data format"""

    def test_save_to_s3(self):
        """Test save to s3"""

    def test_save_to_s3_client_error(self):
        """Test save top s3 with client error"""


if __name__ == "__main__":
    unittest.main()
