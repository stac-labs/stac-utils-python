import json
import unittest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

from src.stac_utils.aws import (
    get_secret,
    write_secret,
    load_from_s3,
    save_to_s3,
    split_s3_url,
)


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
        mock_session.client.assert_called_once_with(
            service_name="secretsmanager", region_name=test_region
        )

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

        mock_session.client.put_secret_value(
            SecretId=test_secret_name, SecretString=json.dumps(test_secret)
        )
        mock_session.client.assert_called_once_with(
            service_name="secretsmanager", region_name=test_region
        )

    @patch("json.load")
    @patch("src.stac_utils.aws.open")
    @patch("boto3.resource")
    def test_load_from_s3(
        self, mock_boto: MagicMock, mock_open: MagicMock, mock_load: MagicMock
    ):
        """Test load from s3"""
        mock_data = {"foo": "bar"}
        mock_load.return_value = mock_data
        result_data = load_from_s3("foo", "bar", "spam")
        self.assertEqual(mock_data, result_data)
        mock_boto.return_value.Bucket.return_value.download_file.assert_called_once()
        self.assertEqual(
            mock_boto.return_value.Bucket.return_value.download_file.call_args[0][0],
            "bar/spam",
        )

    @patch("json.load")
    @patch("src.stac_utils.aws.open")
    @patch("boto3.resource")
    def test_load_from_s3_no_path(
        self, mock_boto: MagicMock, mock_open: MagicMock, mock_load: MagicMock
    ):
        """Test load from s3 when path is None"""
        mock_data = {"foo": "bar"}
        mock_load.return_value = mock_data
        result_data = load_from_s3("foo", None, "spam")
        self.assertEqual(mock_data, result_data)
        mock_boto.return_value.Bucket.return_value.download_file.assert_called_once()
        self.assertEqual(
            mock_boto.return_value.Bucket.return_value.download_file.call_args[0][0],
            "spam",
        )

    @patch("json.load")
    @patch("src.stac_utils.aws.open")
    @patch("boto3.resource")
    def test_load_from_s3_expired_token(
        self, mock_boto: MagicMock, mock_open: MagicMock, mock_load: MagicMock
    ):
        """Test load from s3 with expired token"""
        mock_data = {"foo": "bar"}
        mock_load.return_value = mock_data
        mock_boto.return_value.Bucket.return_value.download_file.side_effect = (
            ClientError({"Error": {"Message": "ExpiredToken"}}, "foo")
        )
        self.assertRaises(ClientError, load_from_s3, "foo", "bar", "spam")

    @patch("json.load")
    @patch("src.stac_utils.aws.open")
    @patch("boto3.resource")
    def test_load_from_s3_client_error(
        self, mock_boto: MagicMock, mock_open: MagicMock, mock_load: MagicMock
    ):
        """Test load from s3 with client error"""
        mock_data = {"foo": "bar"}
        mock_load.return_value = mock_data
        mock_boto.return_value.Bucket.return_value.download_file.side_effect = (
            ClientError({"Error": {"Message": "spam"}}, "foo")
        )
        result_data = load_from_s3("foo", "bar", "spam")
        self.assertEqual({}, result_data)

    @patch("json.load")
    @patch("src.stac_utils.aws.open")
    @patch("boto3.resource")
    def test_load_from_s3_json_decoder_error(
        self, mock_boto: MagicMock, mock_open: MagicMock, mock_load: MagicMock
    ):
        """Test load from s3 with bad data format"""
        mock_load.side_effect = json.JSONDecodeError("foo", "bar", 0)
        result_data = load_from_s3("foo", "bar", "spam")
        self.assertEqual({}, result_data)

    @patch("json.dump")
    @patch("src.stac_utils.aws.open")
    @patch("boto3.resource")
    def test_save_to_s3(
        self, mock_boto: MagicMock, mock_open: MagicMock, mock_dump: MagicMock
    ):
        """Test save to s3"""
        mock_data = {"foo": "bar"}
        result_data = save_to_s3(mock_data, "foo", "bar", "spam")
        mock_boto.return_value.Bucket.return_value.upload_file.assert_called_once()
        self.assertIs(mock_data, result_data)

    @patch("json.dump")
    @patch("src.stac_utils.aws.open")
    @patch("boto3.resource")
    def test_save_to_s3_client_error(
        self, mock_boto: MagicMock, mock_open: MagicMock, mock_dump: MagicMock
    ):
        """Test save to s3 with client error"""
        mock_data = {"foo": "bar"}
        mock_boto.return_value.Bucket.return_value.upload_file.side_effect = (
            ClientError({"Error": {"Message": "spam"}}, "foo")
        )
        self.assertRaises(ClientError, save_to_s3, mock_data, "foo", "bar", "spam")

    def test_split_s3_url(self):
        """Test split S3 url"""

        test_url = "s3://foo-bucket/bar-path/spam-key.json"
        self.assertTupleEqual(
            split_s3_url(test_url), ("foo-bucket", "bar-path", "spam-key.json")
        )

    def test_split_s3_url_no_prefix(self):
        """Test split S3 url with no prefix"""

        test_url = "foo-bucket/bar-path/spam-key.json"
        self.assertTupleEqual(
            split_s3_url(test_url), ("foo-bucket", "bar-path", "spam-key.json")
        )

    def test_split_s3_url_no_path(self):
        """Test split S3 url with no path"""

        test_url = "s3://foo-bucket/spam-key.json"
        self.assertTupleEqual(
            split_s3_url(test_url), ("foo-bucket", "", "spam-key.json")
        )


if __name__ == "__main__":
    unittest.main()
