import os
import unittest
from unittest.mock import patch

from src.stac_utils.secret_context import secrets
from src.stac_utils.listify import listify
from src.stac_utils.convert import convert_to_snake_case
from src.stac_utils.truthy import truthy


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
        self.assertEqual(listify(None), [])

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

    def test_convert_to_snake_case_string(self):
        self.assertEqual(convert_to_snake_case("FooBar"), "foo_bar")
        self.assertEqual(convert_to_snake_case("foo_bar"), "foo_bar")
        self.assertEqual(convert_to_snake_case("FOOBar"), "foo_bar")
        self.assertEqual(convert_to_snake_case("fooBar"), "foo_bar")
        self.assertEqual(convert_to_snake_case("FooBar"), "foo_bar")
        self.assertEqual(convert_to_snake_case("Spam"), "spam")
        self.assertEqual(convert_to_snake_case("spam"), "spam")
        self.assertEqual(convert_to_snake_case(""), "")

    def test_convert_to_snake_case_list(self):
        self.assertEqual(convert_to_snake_case(["FooBar"]), ["foo_bar"])
        self.assertEqual(convert_to_snake_case(["FooBar", "FooBar"]), ["foo_bar", "foo_bar"])
        self.assertEqual(convert_to_snake_case(["Spam"]), ["spam"])
        self.assertEqual(convert_to_snake_case([""]), [""])
        self.assertEqual(convert_to_snake_case([]), [])

    def test_convert_to_snake_case_dict(self):
        self.assertEqual(convert_to_snake_case({"FooBar": "FooBar"}), {"foo_bar": "FooBar"})
        self.assertEqual(convert_to_snake_case({"FooBar": "FooBar", "SpamBar": True}), {"foo_bar": "FooBar", "spam_bar": True})

    def test_convert_to_snake_case_mixed(self):
        self.assertEqual(convert_to_snake_case([{"FooBar": "FooBar"}]), [{"foo_bar": "FooBar"}])
        self.assertEqual(convert_to_snake_case({"Spam": ["FooBar", "FooBar"]}), {"spam": ["foo_bar", "foo_bar"]})

    def test_truthy_true(self):
        self.assertTrue(truthy("True"))
        self.assertTrue(truthy("T"))
        self.assertTrue(truthy("1"))
        self.assertTrue(truthy(1))
        self.assertTrue(truthy("Yes"))
        self.assertTrue(truthy("Y"))
        self.assertTrue(truthy("y"))
        self.assertTrue(truthy("t"))
        self.assertTrue(truthy("true"))
        self.assertTrue(truthy("TRUE"))
        self.assertTrue(truthy("YES"))

    def test_truthy_false(self):
        self.assertFalse(truthy(False))
        self.assertFalse(truthy("False"))
        self.assertFalse(truthy("false"))
        self.assertFalse(truthy("test"))
        self.assertFalse(truthy("Truee"))
        self.assertFalse(truthy(None))
        self.assertFalse(truthy(0))
        self.assertFalse(truthy(11))
        self.assertFalse(truthy("11"))
        self.assertFalse(truthy([]))
        self.assertFalse(truthy(["True"]))
        self.assertFalse(truthy({"True"}))
        self.assertFalse(truthy({"True": 1}))

    def test_truthy_custom(self):
        custom_values = ["FOO", "BAR"]
        self.assertTrue(truthy("foo", custom_values))
        self.assertTrue(truthy("bar", custom_values))
        self.assertTrue(truthy("Foo", custom_values))
        self.assertTrue(truthy("Bar", custom_values))
        self.assertTrue(truthy("FOO", custom_values))
        self.assertTrue(truthy("BAR", custom_values))

        self.assertFalse(truthy("True", custom_values))
        self.assertFalse(truthy("T", custom_values))
        self.assertFalse(truthy("1", custom_values))
        self.assertFalse(truthy(1, custom_values))
        self.assertFalse(truthy("Yes", custom_values))
        self.assertFalse(truthy("Y", custom_values))
        self.assertFalse(truthy("y", custom_values))
        self.assertFalse(truthy("t", custom_values))
        self.assertFalse(truthy("true", custom_values))
        self.assertFalse(truthy("TRUE", custom_values))
        self.assertFalse(truthy("YES", custom_values))
        self.assertFalse(truthy(False, custom_values))
        self.assertFalse(truthy("False", custom_values))
        self.assertFalse(truthy("false", custom_values))
        self.assertFalse(truthy("test", custom_values))
        self.assertFalse(truthy(None, custom_values))
        self.assertFalse(truthy(0, custom_values))
        self.assertFalse(truthy(11, custom_values))
        self.assertFalse(truthy("11", custom_values))
        self.assertFalse(truthy([], custom_values))
        self.assertFalse(truthy(["True"], custom_values))
        self.assertFalse(truthy({"True"}, custom_values))
        self.assertFalse(truthy({"True": 1}, custom_values))


if __name__ == "__main__":
    unittest.main()
