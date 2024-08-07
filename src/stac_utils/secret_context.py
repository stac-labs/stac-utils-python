import json
import os
from unittest.mock import patch

from .aws import get_secret, split_s3_url, load_from_s3


def secrets(
    file_name: str = None,
    secret_name: str = None,
    aws_region: str = None,
    dictionary: dict = None,
    s3_url: str = None,
):
    """
    Takes any combination of
        * local JSON file
        * Python dictionary
        * AWS secret in Secrets Manager
        * JSON file on S3
    and loads it all into the os.environ as a context.

    Usage is typically:

        with secrets('secrets.json'):
            rest_of_code

    :param file_name: Desired file name
    :param secret_name: Desired secret_name
    :param aws_region: Desired AWS region for secret
    :param dictionary: Specified dictionary
    :param s3_url: S3 URL to JSON file
    :return:
    """

    values = {}
    if not secret_name and os.environ.get("SECRET_NAME"):
        secret_name = os.environ.get("SECRET_NAME")
        # blank secret name in the context, so it doesn't get loaded a second time
        # if we nest secrets
        values["SECRET_NAME"] = ""

    if secret_name:
        values.update(
            get_secret(
                aws_region or os.environ.get("AWS_REGION") or "us-east-1",
                secret_name or os.environ["SECRET_NAME"],
            )
        )
    if not s3_url and os.environ.get("SECRET_S3_URL"):
        s3_url = os.environ.get("SECRET_S3_URL")
        # blank secret s3 url in the context, so it doesn't get loaded a second time
        # if we nest secrets
        values["SECRET_S3_URL"] = ""

    if s3_url:
        values.update(load_from_s3(*split_s3_url(s3_url)))

    if file_name:
        values.update(json.load(open(file_name, "rt")))
    if dictionary:
        values.update(dictionary)

    # the patcher doesn't like non-string keys OR values
    values = {
        str(k): safe_dump_json_to_string(v) if v is not None else ""
        for k, v in values.items()
    }

    return patch.dict(os.environ, values=values)


def safe_dump_json_to_string(value: [list, dict, str, int, tuple, float, None]) -> str:
    """Utility function to encode values to string, working through nested dictionaries & list"""

    if type(value) in [dict]:
        return json.dumps(
            {str(k): safe_dump_json_to_string(v) for k, v in value.items()}
        )

    if type(value) in [list, tuple]:
        return json.dumps([safe_dump_json_to_string(v) for v in value])

    if value is None:
        return "null"

    return str(value)


def safe_load_string_to_json(value: str) -> [list, dict, str, int, float, None]:
    """Utility function to decode values from string, restoring all nested dictionaries & list"""

    try:
        loaded = json.loads(value)
    except (json.decoder.JSONDecodeError, TypeError):
        loaded = value

    if type(loaded) in [dict]:
        return {k: safe_load_string_to_json(v) for k, v in loaded.items()}

    if type(loaded) in [list]:
        return [safe_load_string_to_json(v) for v in loaded]

    return loaded


def get_env(key: str, default=None) -> [list, dict, str]:
    """Utility function combining os.environ.get & safe_load_from_json"""

    value = os.environ.get(key, default=default)

    return safe_load_string_to_json(value)
