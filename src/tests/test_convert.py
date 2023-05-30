import unittest

from src.stac_utils.convert import convert_to_snake_case


class TestConvert(unittest.TestCase):
    def test_convert_to_snake_case_string(self):
        self.assertEqual("foo_bar", convert_to_snake_case("FooBar"))
        self.assertEqual("foo_bar", convert_to_snake_case("foo_bar"))
        self.assertEqual("foo_bar", convert_to_snake_case("FOOBar"))
        self.assertEqual("foo_bar", convert_to_snake_case("fooBar"))
        self.assertEqual("foo_bar", convert_to_snake_case("FooBar"))
        self.assertEqual("spam", convert_to_snake_case("Spam"))
        self.assertEqual("spam", convert_to_snake_case("spam"))
        self.assertEqual("", convert_to_snake_case(""))

    def test_convert_to_snake_case_list(self):
        self.assertEqual(["foo_bar"], convert_to_snake_case(["FooBar"]))
        self.assertEqual(
            ["foo_bar", "foo_bar"], convert_to_snake_case(["FooBar", "FooBar"])
        )
        self.assertEqual(["spam"], convert_to_snake_case(["Spam"]))
        self.assertEqual([""], convert_to_snake_case([""]))
        self.assertEqual([], convert_to_snake_case([]))

    def test_convert_to_snake_case_dict(self):
        self.assertEqual(
            {"foo_bar": "FooBar"},
            convert_to_snake_case({"FooBar": "FooBar"}),
        )
        self.assertEqual(
            {"foo_bar": "FooBar", "spam_bar": True},
            convert_to_snake_case({"FooBar": "FooBar", "SpamBar": True}),
        )

    def test_convert_to_snake_case_mixed(self):
        self.assertEqual(
            [{"foo_bar": "FooBar"}], convert_to_snake_case([{"FooBar": "FooBar"}])
        )
        self.assertEqual(
            {"spam": ["foo_bar", "foo_bar"]},
            convert_to_snake_case({"Spam": ["FooBar", "FooBar"]}),
        )


if __name__ == "__main__":
    unittest.main()
