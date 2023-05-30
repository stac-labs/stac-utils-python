import os
import unittest
from datetime import datetime
from unittest.mock import patch

from dateutil.tz import tzfile
from freezegun import freeze_time

from src.stac_utils.time import (
    parse_date_for_tz,
    get_today_tz,
    get_now_tz,
    DEFAULT_TIMEZONE,
)


class TestTime(unittest.TestCase):
    def test_parse_date_for_tz(self):
        """Test parse date for date time using default eastern time zone"""
        self.assertEqual(DEFAULT_TIMEZONE, "America/New_York")
        self.assertEqual(
            datetime(
                2023, 1, 1, 0, 0, tzinfo=tzfile("/usr/share/zoneinfo/America/New_York")
            ),
            parse_date_for_tz("2023-01-01"),
        )

    def test_parse_date_for_tz_environment_tz(self):
        """Test parse date for time zone using environment's timezone"""

        test_tz_dict = {"TIMEZONE": "America/Los_Angeles"}

        with patch.dict(os.environ, values=test_tz_dict):
            self.assertEqual(
                datetime(
                    2023,
                    1,
                    1,
                    0,
                    0,
                    tzinfo=tzfile("/usr/share/zoneinfo/America/Los_Angeles"),
                ),
                parse_date_for_tz("2023-01-01"),
            )

    @freeze_time("2023-01-01", tz_offset=5)
    def test_get_today_tz(self):
        """Get today's date with time zone"""
        self.assertEqual(
            datetime(
                2023, 1, 1, 0, 0, tzinfo=tzfile("/usr/share/zoneinfo/America/New_York")
            ),
            get_today_tz(),
        )

    @freeze_time("2023-01-01 12:00:01", tz_offset=5)
    def test_get_now_tz(self):
        """Get current date and time with time zone"""
        self.assertEqual(
            datetime(
                2023,
                1,
                1,
                12,
                0,
                1,
                tzinfo=tzfile("/usr/share/zoneinfo/America/New_York"),
            ),
            get_now_tz(),
        )


if __name__ == "__main__":
    unittest.main()
