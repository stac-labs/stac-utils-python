import unittest

from src.stac_utils.convert import convert_to_snake_case


class TestConvert(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
