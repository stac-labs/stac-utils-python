import json
import unittest
from unittest.mock import MagicMock, patch, call

from src.stac_utils.aws import get_secret, write_secret, load_from_s3, save_to_s3


class TestAWS(unittest.TestCase):
    @patch("boto3.session.Session")
    def test_get_secret(self, mock_session_class: MagicMock):
        """Test get secret"""

        test_region = "us-east-1"
        test_secret_name = "spam"
        test_secret = {"FOO": "bar"}
        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client = MagicMock(return_value=mock_client)
        mock_client.get_secret_value = MagicMock(
            return_value={"SecretString": json.dumps(test_secret)}
        )
        test_response = get_secret(test_region, test_secret_name)

        self.assertEqual(test_response, test_secret)
        mock_session.client.get_secret_value(SecretId=test_secret_name)
        mock_session.client.assert_called_once_with(service_name='secretsmanager', region_name=test_region)

    @patch("boto3.session.Session")
    def test_write_secret(self, mock_session_class: MagicMock):
        """Test write secret"""

        test_region = "us-east-1"
        test_secret_name = "spam"
        test_secret = {"FOO": "bar"}
        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client = MagicMock(return_value=mock_client)
        mock_client.put_secret_value = MagicMock()
        write_secret(test_region, test_secret_name, test_secret)

        mock_session.client.put_secret_value(SecretId=test_secret_name, SecretString=json.dumps(test_secret))
        mock_session.client.assert_called_once_with(service_name='secretsmanager', region_name=test_region)

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
