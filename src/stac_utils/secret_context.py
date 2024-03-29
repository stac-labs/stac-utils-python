import json
import os
from unittest.mock import patch

from .aws import get_secret


def secrets(
    file_name: str = None,
    secret_name: str = None,
    aws_region: str = None,
    dictionary: dict = None,
):
    """
    Takes either a file, a Python dict, or an AWS secret in Secrets Manager and loads it all into the os.environ as a context.

    Usage is typically:

        with secrets('secrets.json'):
            rest_of_code

    :param file_name: Desired file name
    :param secret_name: Desired secret_name
    :param aws_region: Desired AWS region for secret
    :param dictionary: Specified dictionary
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

    if file_name:
        values.update(json.load(open(file_name, "rt")))
    if dictionary:
        values.update(dictionary)

    # the patcher doesn't like non-string keys OR values
    values = {str(k): str(v) if v is not None else "" for k, v in values.items()}
    return patch.dict(os.environ, values=values)
