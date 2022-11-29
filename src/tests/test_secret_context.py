import os
import unittest
from unittest.mock import patch

from src.stac_utils.secret_context import secrets


class TestSecretsContext(unittest.TestCase):
    def test_secrets(self):
        """Test that secrets context manager works"""

        with secrets():
            pass

    @patch("src.stac_utils.secret_context.get_secret")
    def test_secrets_aws_secret(self, mock_get_secret):
        """Test that AWS secrets"""
        mock_get_secret.return_value = {"FOO": "BAR"}
        with patch.dict(
            os.environ,
            values={"AWS_REGION": "us-east-1", "SECRET_NAME": "spam-credentials"},
        ):
            with secrets():
                self.assertEqual(os.environ["FOO"], "BAR")
        mock_get_secret.assert_called_once_with("us-east-1", "spam-credentials")

    @patch("src.stac_utils.secret_context.get_secret")
    def test_secrets_aws_secret_parameter_name(self, mock_get_secret):
        """Test loading secrets specified in parameter over environ SECRET_NAME"""
        mock_get_secret.return_value = {"FOO": "BAR"}
        with patch.dict(
            os.environ,
            values={"AWS_REGION": "us-east-1", "SECRET_NAME": "spam-credentials"},
        ):
            with secrets(aws_region="us-west-2", secret_name="foo-credentials"):
                self.assertEqual(os.environ["FOO"], "BAR")
        mock_get_secret.assert_called_once_with("us-west-2", "foo-credentials")

    def test_secrets_json_secrets(self):
        """Test loading json secrets"""

        with secrets(file_name="src/tests/mock-credentials.json"):
            self.assertEqual(os.environ["FOO"], "BAR")

    def test_secrets_dictionary_secrets(self):
        """Test loading dictionary secrets"""

        test_dict = {"FOO": "BAR"}
        with secrets(dictionary=test_dict):
            self.assertEqual(os.environ["FOO"], "BAR")

    @patch("src.stac_utils.secret_context.get_secret")
    def test_secrets_priority_order(self, mock_get_secret):
        """Test that secrets from AWS, dictionary & files are prioritized correctly
        Dictionary > File > AWS parameter secret > AWS environ secret > os.environ
        """

        mock_get_secret.return_value = {"FOO": "NO"}
        test_dict = {"FOO": "SPAM"}
        with patch.dict(
            os.environ,
            values={"AWS_REGION": "us-east-1", "SECRET_NAME": "spam-credentials"},
        ):
            with secrets(
                dictionary=test_dict,
                file_name="src/tests/mock-credentials.json",
                aws_region="us-west-2",
                secret_name="foo-credentials",
            ):
                self.assertEqual(os.environ["FOO"], "SPAM")

    def test_secrets_nested(self):
        """Test that secrets can be nested"""

        test_dict = {"FOO": "NO"}
        with secrets(dictionary=test_dict):
            with secrets(file_name="src/tests/mock-credentials.json"):
                self.assertEqual(os.environ["FOO"], "BAR")

    @patch("src.stac_utils.secret_context.get_secret")
    def test_secrets_nested_aws_secret(self, mock_get_secret):
        """Test that SECRET_NAME gets popped off os.environ once an AWS secret has been loaded"""

        mock_get_secret.return_value = {"FOO": "BAR"}
        test_dict = {"FOO": "SPAM"}
        with patch.dict(
            os.environ,
            values={"AWS_REGION": "us-east-1", "SECRET_NAME": "spam-credentials"},
        ):
            with secrets():
                self.assertEqual(os.environ["SECRET_NAME"], "")
                with secrets(dictionary=test_dict):
                    self.assertEqual(os.environ["FOO"], "SPAM")

        mock_get_secret.assert_called_once_with("us-east-1", "spam-credentials")

    def test_secrets_null(self):
        """Test that null secrets don't break everything"""
        test_dict = {"FOO": None}
        with secrets(dictionary=test_dict):
            pass


if __name__ == '__main__':
    unittest.main()
