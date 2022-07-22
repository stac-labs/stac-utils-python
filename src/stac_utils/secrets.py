import os
import json
from unittest.mock import patch

from .aws import get_secret

def secrets(
    file_name: str = None,
    secret_name: str = None,
    aws_region: str = None,
    dictionary: dict = None,
):
    values = {}
    if dictionary:
        values.update(dictionary)
    if file_name:
        values.update(json.load(open(file_name, "rt")))
    if secret_name or os.environ.get("SECRET_NAME"):
        values.update(
            get_secret(
                aws_region or os.environ.get("AWS_REGION") or "us-east-1",
                secret_name or os.environ["SECRET_NAME"],
            )
        )

    # the patcher doesn't like non-string keys OR values
    values = {str(k): str(v) for k, v in values.items()}
    return patch.dict(os.environ, values=values)
