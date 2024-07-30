import json
import logging
import os.path as op
from tempfile import TemporaryDirectory

import boto3
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)


def get_secret(region_name: str, secret_name: str) -> dict:
    # Create a Secrets Manager client
    """
    Returns secret given AWS region and name

    :param region_name: Desired AWS region
    :param secret_name: Secret name
    :return: Secret
    """
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    get_secret_value_response = client.get_secret_value(SecretId=secret_name)

    secret = json.loads(get_secret_value_response["SecretString"])

    return secret


def write_secret(region_name: str, secret_name: str, secret: dict):
    # Create a Secrets Manager client
    """
    Writes secret, given AWS region, name, and secret

    :param region_name: Desired AWS region
    :param secret_name: Secret name
    :param secret: AWS secret
    """
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    client.put_secret_value(
        SecretId=secret_name,
        SecretString=json.dumps(secret),
    )


def split_s3_url(url: str) -> tuple[str, str, str]:
    prefix = "s3://"
    if url.startswith(prefix):
        url = url[len(prefix):]

    bucket, _, fpath = url.partition("/")
    path, _, file_name = fpath.rpartition("/")

    return bucket, path, file_name


def load_from_s3(bucket: str, path: str, file_name: str) -> dict:
    """
    Returns data from s3 given bucket, path, and file name

    :param bucket: s3 bucket
    :param path: Path within bucket
    :param file_name: Name of file to load
    :return: Data from specified file
    """
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
            logger.warning(f"{key} is not a JSON file!")
            data = {}

    return data


def save_to_s3(data: dict, bucket: str, path: str, file_name: str):
    """
    Saves data to s3 in specified location

    :param data: Data to load to s3
    :param bucket: s3 bucket
    :param path: Path within bucket
    :param file_name: Desired file name
    :return: Data
    """
    s3 = boto3.resource("s3").Bucket(bucket)
    key = path.strip("/") + "/" + file_name

    with TemporaryDirectory() as temp:
        temp_file = op.join(temp, file_name)
        json.dump(data, open(temp_file, "wt"), indent=4)
        s3.upload_file(temp_file, Key=key)

    return data
