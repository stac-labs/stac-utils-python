import os
from datetime import datetime

from dateutil.utils import default_tzinfo, today as _today
from dateutil.parser import parse as _parse
from dateutil.tz import gettz

DEFAULT_TIMEZONE = "America/New_York"


def parse_date_for_tz(value: str) -> datetime:
    """
    Parse date adjusting for timezone if timezone is not present

    :return: Parsed date (adjusted for timezone if no timezone present)
    """
    timezone = gettz(os.environ.get("TIMEZONE", DEFAULT_TIMEZONE))

    return default_tzinfo(_parse(value), timezone)


def get_today_tz() -> datetime:
    """
    Shortcut for getting today's date in the timezone specified by the 'TIMEZONE' environment variable

    :return: Today's date in timezone specified by environment variable
    """
    timezone = gettz(os.environ.get("TIMEZONE", DEFAULT_TIMEZONE))

    return _today(timezone)


def get_now_tz() -> datetime:
    """
    Shortcut for getting the current time in the timezone specified by the 'TIMEZONE' environment variable

    :return: Current time in timezone specified by environment variable
    """
    timezone = gettz(os.environ.get("TIMEZONE", DEFAULT_TIMEZONE))

    return datetime.now(timezone)
