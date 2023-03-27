import json
import os.path as op
from tempfile import TemporaryDirectory

import boto3
from botocore.exceptions import ClientError


def get_secret(region_name: str, secret_name: str) -> dict:
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    get_secret_value_response = client.get_secret_value(SecretId=secret_name)

    secret = json.loads(get_secret_value_response["SecretString"])

    return secret


def write_secret(region_name: str, secret_name: str, secret: dict):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    client.put_secret_value(
        SecretId=secret_name,
        SecretString=json.dumps(secret),
    )


def load_from_s3(bucket: str, path: str, file_name: str) -> dict:
    s3 = boto3.resource("s3").Bucket(bucket)
    key = path.strip("/") + "/" + file_name

    data = {}
    with TemporaryDirectory() as temp:
        temp_file = op.join(temp, file_name)
        try:
            s3.download_file(key, temp_file)
            data = json.load(open(temp_file))
        except ClientError as e:
            if "ExpiredToken" in str(e):
                raise e
            data = {}
        except json.JSONDecodeError:
            data = {}

    return data


def save_to_s3(data: dict, bucket: str, path: str, file_name: str):
    s3 = boto3.resource("s3").Bucket(bucket)
    key = path.strip("/") + "/" + file_name

    with TemporaryDirectory() as temp:
        temp_file = op.join(temp, file_name)
        json.dump(data, open(temp_file, "wt"), indent=4)
        s3.upload_file(temp_file, Key=key)

    return data
