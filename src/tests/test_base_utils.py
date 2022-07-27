import os
import unittest
from unittest.mock import patch

from src.stac_utils.secret_context import secrets
from src.stac_utils.listify import listify
from src.stac_utils.convert import convert_to_snake_case


class TestBaseUtils(unittest.TestCase):
    def test_listify(self):
        self.assertListEqual(listify("foo,bar"), ["foo", "bar"])
        self.assertListEqual(listify("foo, bar"), ["foo", "bar"])
        self.assertListEqual(listify(" foo,bar "), ["foo", "bar"])
        self.assertListEqual(listify(" foo,bar "), ["foo", "bar"])
        self.assertListEqual(listify("foo,bar,"), ["foo", "bar"])
        self.assertListEqual(listify("foo,bar,,"), ["foo", "bar"])
        self.assertListEqual(listify("foo"), ["foo"])
        self.assertListEqual(listify(""), [])

    def test_listify_none(self):
        self.assertEquals(listify(None), [])

    def test_listify_other_types(self):
        self.assertListEqual(listify("foo,bar", type_=str), ["foo", "bar"])
        self.assertListEqual(listify("1,2", type_=int), [1, 2])
        self.assertListEqual(listify("1,2", type_=float), [1.0, 2.0])
        self.assertListEqual(listify("1.5,2", type_=float), [1.5, 2.0])
        self.assertRaises(ValueError, lambda: listify("foo,bar", type_=int))
        self.assertRaises(ValueError, lambda: listify("1.5,2.0", type_=int))

    def test_listify_ignore_empty(self):
        self.assertListEqual(listify("foo,bar", ignore_empty=False), ["foo", "bar"])
        self.assertListEqual(
            listify("foo,bar,", ignore_empty=False), ["foo", "bar", ""]
        )
        self.assertListEqual(
            listify("foo,bar,,", ignore_empty=False), ["foo", "bar", "", ""]
        )
        self.assertListEqual(listify("", ignore_empty=True), [])

    def test_listify_ignore_errors(self):
        self.assertListEqual(listify("foo,bar", ignore_errors=True), ["foo", "bar"])
        self.assertListEqual(listify("1,2,spam", type_=int, ignore_errors=True), [1, 2])
        self.assertListEqual(listify("1,2,", type_=int, ignore_errors=True), [1, 2])
        self.assertListEqual(
            listify("1,2,spam", type_=int, ignore_errors=True, ignore_empty=False),
            [1, 2, None],
        )
        self.assertListEqual(listify("", ignore_errors=True), [])

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
                self.assertEquals(os.environ["FOO"], "BAR")
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
                self.assertEquals(os.environ["FOO"], "BAR")
        mock_get_secret.assert_called_once_with("us-west-2", "foo-credentials")

    def test_secrets_json_secrets(self):
        """Test loading json secrets"""

        with secrets(file_name="mock-credentials.json"):
            self.assertEquals(os.environ["FOO"], "BAR")

    def test_secrets_dictionary_secrets(self):
        """Test loading dictionary secrets"""

        test_dict = {"FOO": "BAR"}
        with secrets(dictionary=test_dict):
            self.assertEquals(os.environ["FOO"], "BAR")

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
                file_name="mock-credentials.json",
                aws_region="us-west-2",
                secret_name="foo-credentials",
            ):
                self.assertEquals(os.environ["FOO"], "SPAM")

    def test_secrets_nested(self):
        """Test that secrets can be nested"""

        test_dict = {"FOO": "NO"}
        with secrets(dictionary=test_dict):
            with secrets(file_name="mock-credentials.json"):
                self.assertEquals(os.environ["FOO"], "BAR")

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
                self.assertEquals(os.environ["SECRET_NAME"], "")
                with secrets(dictionary=test_dict):
                    self.assertEquals(os.environ["FOO"], "SPAM")

        mock_get_secret.assert_called_once_with("us-east-1", "spam-credentials")

    def test_secrets_null(self):
        """Test that null secrets don't break everything"""
        test_dict = {"FOO": None}
        with secrets(dictionary=test_dict):
            pass

    def test_convert_to_snake_case_string(self):
        self.assertEquals(convert_to_snake_case("FooBar"), "foo_bar")
        self.assertEquals(convert_to_snake_case("foo_bar"), "foo_bar")
        self.assertEquals(convert_to_snake_case("FOOBar"), "foo_bar")
        self.assertEquals(convert_to_snake_case("fooBar"), "foo_bar")
        self.assertEquals(convert_to_snake_case("FooBar"), "foo_bar")
        self.assertEquals(convert_to_snake_case("Spam"), "spam")
        self.assertEquals(convert_to_snake_case("spam"), "spam")
        self.assertEquals(convert_to_snake_case(""), "")

    def test_convert_to_snake_case_list(self):
        self.assertEquals(convert_to_snake_case(["FooBar"]), ["foo_bar"])
        self.assertEquals(convert_to_snake_case(["FooBar", "FooBar"]), ["foo_bar", "foo_bar"])
        self.assertEquals(convert_to_snake_case(["Spam"]), ["spam"])
        self.assertEquals(convert_to_snake_case([""]), [""])
        self.assertEquals(convert_to_snake_case([]), [])

    def test_convert_to_snake_case_dict(self):
        self.assertEquals(convert_to_snake_case({"FooBar": "FooBar"}), {"foo_bar": "FooBar"})
        self.assertEquals(convert_to_snake_case({"FooBar": "FooBar", "SpamBar": True}), {"foo_bar": "FooBar", "spam_bar": True})

    def test_convert_to_snake_case_mixed(self):
        self.assertEquals(convert_to_snake_case([{"FooBar": "FooBar"}]), [{"foo_bar": "FooBar"}])
        self.assertEquals(convert_to_snake_case({"Spam": ["FooBar", "FooBar"]}), {"spam": ["foo_bar", "foo_bar"]})


if __name__ == "__main__":
    unittest.main()
