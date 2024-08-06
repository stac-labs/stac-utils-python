import os
import unittest
from unittest.mock import patch, MagicMock

from src.stac_utils.secret_context import (
    secrets,
    safe_load_string_to_json,
    safe_dump_json_to_string,
    get_env,
)


class TestSecretsContext(unittest.TestCase):
    def test_secrets(self):
        """Test that secrets context manager works"""

        with secrets():
            pass

    @patch("src.stac_utils.secret_context.get_secret")
    def test_secrets_aws_secret(self, mock_get_secret: MagicMock):
        """Test that AWS secrets"""
        mock_get_secret.return_value = {"FOO": "BAR"}
        with patch.dict(
            os.environ,
            values={"AWS_REGION": "us-east-1", "SECRET_NAME": "spam-credentials"},
        ):
            with secrets():
                self.assertEqual("BAR", os.environ["FOO"])
        mock_get_secret.assert_called_once_with("us-east-1", "spam-credentials")

    @patch("src.stac_utils.secret_context.get_secret")
    def test_secrets_aws_secret_parameter_name(self, mock_get_secret: MagicMock):
        """Test loading secrets specified in parameter over environ SECRET_NAME"""
        mock_get_secret.return_value = {"FOO": "BAR"}
        with patch.dict(
            os.environ,
            values={"AWS_REGION": "us-east-1", "SECRET_NAME": "spam-credentials"},
        ):
            with secrets(aws_region="us-west-2", secret_name="foo-credentials"):
                self.assertEqual("BAR", os.environ["FOO"])
        mock_get_secret.assert_called_once_with("us-west-2", "foo-credentials")

    @patch("src.stac_utils.secret_context.load_from_s3")
    def test_secrets_s3_url(self, mock_load_from_s3: MagicMock):
        """Test that S3 URL works from env"""
        mock_load_from_s3.return_value = {"FOO": "BAR"}
        with patch.dict(
            os.environ,
            values={"SECRET_S3_URL": "foo/bar/spam"},
        ):
            with secrets():
                self.assertEqual("BAR", os.environ["FOO"])
        mock_load_from_s3.assert_called_once_with("foo", "bar", "spam")

    @patch("src.stac_utils.secret_context.load_from_s3")
    def test_secrets_s3_url_parameter_name(self, mock_load_from_s3: MagicMock):
        """Test loading secrets specified in parameter over environ SECRET_S3_URL"""
        mock_load_from_s3.return_value = {"FOO": "BAR"}
        with patch.dict(
            os.environ,
            values={"SECRET_S3_URL": "foo/bar/spam"},
        ):
            with secrets(s3_url="foo/bar/spam"):
                self.assertEqual("BAR", os.environ["FOO"])
        mock_load_from_s3.assert_called_once_with("foo", "bar", "spam")

    def test_secrets_json_secrets(self):
        """Test loading json secrets"""

        with secrets(file_name="src/tests/mock-credentials.json"):
            self.assertEqual("BAR", os.environ["FOO"])

    def test_secrets_dictionary_secrets(self):
        """Test loading dictionary secrets"""

        test_dict = {"FOO": "BAR"}
        with secrets(dictionary=test_dict):
            self.assertEqual("BAR", os.environ["FOO"])

    @patch("src.stac_utils.secret_context.load_from_s3")
    @patch("src.stac_utils.secret_context.get_secret")
    def test_secrets_priority_order(
        self, mock_get_secret: MagicMock, mock_load_from_s3: MagicMock
    ):
        """Test that secrets from AWS, dictionary & files are prioritized correctly
        Dictionary > File > S3 URL secret > AWS secret > os.environ
        """

        mock_get_secret.return_value = {"FOO": "NO"}
        mock_load_from_s3.return_value = {"FOO": "BAR"}
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
                s3_url="s3://bar-bucket/spam_path/foo_key.json",
            ):
                self.assertEqual("SPAM", os.environ["FOO"])

    def test_secrets_nested(self):
        """Test that secrets can be nested"""

        test_dict = {"FOO": "NO"}
        with secrets(dictionary=test_dict):
            with secrets(file_name="src/tests/mock-credentials.json"):
                self.assertEqual("BAR", os.environ["FOO"])

    @patch("src.stac_utils.secret_context.get_secret")
    def test_secrets_nested_aws_secret(self, mock_get_secret: MagicMock):
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
                    self.assertEqual("SPAM", os.environ["FOO"])

        mock_get_secret.assert_called_once_with("us-east-1", "spam-credentials")

    def test_secrets_null(self):
        """Test that null secrets don't break everything"""
        test_dict = {"FOO": None}
        with secrets(dictionary=test_dict):
            pass

    def test_safe_dump_and_load(self):
        """Test safe_dump_json_to_string & safe_load_string_to_json basic cases"""

        test_items = [
            {"FOO": "BAR"},
            ["FOO", "BAR"],
            "FOO",
            "",
            1,
            1.1,
            None,
        ]

        for test_item in test_items:
            self.assertEquals(
                test_item, safe_load_string_to_json(safe_dump_json_to_string(test_item))
            )

    def test_test_safe_dump_and_load_nested(self):
        """Test safe_dump_json_to_string & safe_load_string_to_json nested cases"""

        test_items = [
            {"FOO": {"BAR": "SPAM"}},
            [{"FOO": "BAR"}, {"FOO": "BAR"}],
            [{"FOO": {"BAR": "SPAM"}}, {"FOO": {"BAR": "SPAM"}}],
            {"FOO": {"BAR": {"BAR": {"BAR": {"BAR": "SPAM"}}}}},
        ]

        for test_item in test_items:
            self.assertEquals(
                test_item, safe_load_string_to_json(safe_dump_json_to_string(test_item))
            )

    def test_get_env(self):
        """Test get_env"""

        test_env = {"FOO": "BAR"}
        with patch.dict(os.environ, values=test_env):
            self.assertEqual(
                get_env("FOO"),
                test_env["FOO"],
            )

    @patch("src.stac_utils.secret_context.safe_load_string_to_json")
    def test_get_env_safe_load(self, mock_safe_load: MagicMock):
        """Test get_env that it uses safe_load_string_to_json"""

        test_env = {"SPAM": '{"FOO": "BAR"}'}
        mock_safe_load.return_value = {"FOO": "BAR"}
        with patch.dict(os.environ, values=test_env):
            self.assertEqual(
                get_env("SPAM"),
                {"FOO": "BAR"},
            )
            mock_safe_load.assert_called_once_with(test_env["SPAM"])

    def test_get_env_no_value(self):
        """Test get_env when value doesn't exist"""

        test_env = {"FOO": "BAR"}
        with patch.dict(os.environ, values=test_env):
            self.assertIsNone(
                get_env("SPAM"),
            )

    def test_get_env_with_default(self):
        """Test get_env with a provided default"""

        test_env = {"FOO": "BAR"}
        with patch.dict(os.environ, values=test_env):
            self.assertEqual(
                get_env("SPAM", "TOAST"),
                "TOAST",
            )


if __name__ == "__main__":
    unittest.main()
