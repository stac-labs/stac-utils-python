import unittest

from src.stac_utils.eid import convert_to_eid


class TestEid(unittest.TestCase):
    def test_convert_to_eid(self):
        self.assertEqual(convert_to_eid(1), "EID1B")
        self.assertEqual(convert_to_eid(4391), "EID7211F")


if __name__ == "__main__":
    unittest.main()
