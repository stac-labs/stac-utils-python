import unittest


from src.stac_utils.time import parse_date_for_tz, get_today_tz


class TestTime(unittest.TestCase):
    def test_parse_date_for_tz(self):
        """Test parse date for date time using default eastern time zone"""

    def test_parse_date_for_tz_environment_tz(self):
        """Test parse date for time zone using environment's timezone"""

    def test_get_today_tz(self):
        """Get today's date with time zone"""


if __name__ == "__main__":
    unittest.main()
