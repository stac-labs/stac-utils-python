import unittest

from src.stac_utils.listify import listify


class TestListify(unittest.TestCase):
    def test_listify(self):
        self.assertListEqual(["foo", "bar"], listify("foo,bar"))
        self.assertListEqual(["foo", "bar"], listify("foo, bar"))
        self.assertListEqual(["foo", "bar"], listify(" foo,bar "))
        self.assertListEqual(["foo", "bar"], listify(" foo,bar "))
        self.assertListEqual(["foo", "bar"], listify("foo,bar,"))
        self.assertListEqual(["foo", "bar"], listify("foo,bar,,"))
        self.assertListEqual(["foo"], listify("foo"))
        self.assertListEqual([], listify(""))

    def test_listify_none(self):
        self.assertEqual([], listify(None))

    def test_listify_other_types(self):
        self.assertListEqual(["foo", "bar"], listify("foo,bar", type_=str), )
        self.assertListEqual([1, 2], listify("1,2", type_=int))
        self.assertListEqual([1.0, 2.0], listify("1,2", type_=float))
        self.assertListEqual([1.5, 2.0], listify("1.5,2", type_=float))
        self.assertRaises(ValueError, lambda: listify("foo,bar", type_=int))
        self.assertRaises(ValueError, lambda: listify("1.5,2.0", type_=int))

    def test_listify_ignore_empty(self):
        self.assertListEqual(["foo", "bar"], listify("foo,bar", ignore_empty=False))
        self.assertListEqual(
            ["foo", "bar", ""], listify("foo,bar,", ignore_empty=False)
        )
        self.assertListEqual(
            ["foo", "bar", "", ""], listify("foo,bar,,", ignore_empty=False)
        )
        self.assertListEqual([], listify("", ignore_empty=True))

    def test_listify_ignore_errors(self):
        self.assertListEqual(["foo", "bar"], listify("foo,bar", ignore_errors=True))
        self.assertListEqual([1, 2], listify("1,2,spam", type_=int, ignore_errors=True))
        self.assertListEqual([1, 2], listify("1,2,", type_=int, ignore_errors=True))
        self.assertListEqual(
            [1, 2, None],
            listify("1,2,spam", type_=int, ignore_errors=True, ignore_empty=False),
        )
        self.assertListEqual([], listify("", ignore_errors=True))


if __name__ == "__main__":
    unittest.main()
