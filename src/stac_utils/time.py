import os

from datetime import datetime
from dateutil.utils import default_tzinfo, today as _today
from dateutil.parser import parse as _parse
from dateutil.tz import gettz

timezone = gettz(os.environ.get("TIMEZONE", "America/New_York"))


def parse_date_for_tz(value: str) -> datetime:
    """Parse date adjusting for timezone if timezone is not present"""
    return default_tzinfo(_parse(value), timezone)


def get_today_tz() -> datetime:
    """Shortcut for getting today's date in the timezone specified by the 'TIMEZONE' environment variable"""
    return _today(timezone)


def get_now_tz() -> datetime:
    """Shortcut for getting the current time in the timezone specified by the 'TIMEZONE' environment variable"""
    return datetime.now(timezone)
