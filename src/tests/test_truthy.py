import unittest

from src.stac_utils.truthy import truthy


class TestTruthy(unittest.TestCase):
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
