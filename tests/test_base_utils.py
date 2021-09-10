import unittest

from stac_utils import listify


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


if __name__ == "__main__":
    unittest.main()
