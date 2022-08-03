import json
import os
import sys

from typing import Any, List, Union, Mapping, Sequence

from google.cloud import storage, bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build

from .listify import listify


def get_credentials(
    service_account_blob: Mapping = None,
    service_account_env_name: str = "SERVICE_ACCOUNT",
    scopes: Union[Sequence[str], str] = None,
    subject: str = None,
) -> service_account.Credentials:
    """Loads a Google Service Account into a Credentials object with the given scopes"""

    if not service_account_blob:
        service_account_blob = json.loads(os.environ[service_account_env_name])

    if isinstance(scopes, str):
        scopes = listify(scopes)

    _scopes = [
        s if s.startswith("https") else f"https://www.googleapis.com/auth/{s}"
        for s in scopes
    ]
    credentials = service_account.Credentials.from_service_account_info(
        service_account_blob, scopes=_scopes, subject=subject
    )

    return credentials


def auth_bq() -> bigquery.Client:
    """Returns an initialized BigQuery client object"""

    scopes = ["cloud-platform"]
    credentials = get_credentials(scopes=scopes)

    client = bigquery.Client(
        credentials=credentials,
        project=credentials.project_id,
    )

    return client


def run_query(
    sql: str, service_account_blob: Mapping[str, str] = None, subject: str = None, client: bigquery.Client = None,
) -> List[dict]:
    if not client:
        if not service_account_blob:
            service_account_blob = json.loads(os.environ["BQ_SERVICE_ACCOUNT"])

        credentials = get_credentials(
            service_account_blob, scopes=["bigquery", "drive"], subject=subject
        )
        client = bigquery.Client(credentials=credentials)

    job = client.query(sql).result()

    results = [{k: v for k, v in row.items()} for row in job]

    return results


def load_data_from_dataframe(
    client: bigquery.Client,
    dataframe: Any,
    project_name: str,
    dataset_name: str,
    table_name: str,
):
    """Loads data from the specified dataframe into the specified table in BigQuery"""
    dataset_ref = bigquery.Dataset(project_name + "." + dataset_name)
    table_ref = dataset_ref.table(table_name)

    table = client.get_table(table_ref)

    print("inserting rows")

    results = client.insert_rows_from_dataframe(
        table=table, dataframe=dataframe, chunk_size=10000
    )

    print(results)


def auth_gcs() -> storage.Client:
    """Returns an initialized Storage client object"""

    scopes = ["cloud-platform"]
    credentials = get_credentials(scopes=scopes)

    client = storage.Client(
        credentials=credentials,
        project=credentials.project_id,
    )

    return client


def upload_data_to_gcs(
    bucket_name: str, filename: str, destination_filename: str, destination_path: str
):
    """Uploads the given file to a specified path in a GCS Bucket"""
    destination_path = destination_path.strip("/")
    destination_blob_name = destination_path + "/" + destination_filename

    client = auth_gcs()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    if not blob.exists(client):
        print(f"Uploading {filename} to {bucket_name}")
        blob.chunk_size = 5 * 1024 * 1024
        blob.upload_from_filename(filename)

        print("File", filename, "uploaded to GCS as", destination_blob_name)
    else:
        print("Already on GCS", file=sys.stderr)


def make_gmail_client(
    service_account_blob: Mapping[str, str] = None,
    subject: str = None,
    scopes: List[str] = None,
):
    """Returns an initialized Gmail Client object"""

    scopes = scopes or ["gmail.labels", "gmail.modify", "gmail.readonly"]

    credentials = get_credentials(service_account_blob, scopes=scopes, subject=subject)
    return build("gmail", "v1", credentials=credentials)


def _sanitize_name(string: str) -> str:
    valid_chars = "abcdefghijklmnopqrstuvwxyz1234567890._"

    # crudely prevent sql injection
    return "".join([s for s in string.lower() if s in valid_chars])


def get_table(
    table_name: str,
    service_account_blob: Mapping[str, str] = None,
    service_account_env_name: str = "SERVICE_ACCOUNT",
    subject: str = None,
) -> List[dict]:
    """Performs a select * from the given table"""
    if not service_account_blob:
        try:
            service_account_blob = json.loads(os.environ[service_account_env_name])
        except json.JSONDecodeError:
            pass

    # sadly bq's parameterized queries don't support table names
    sql = f"SELECT * FROM `{_sanitize_name(table_name)}`;"
    results = run_query(sql, service_account_blob=service_account_blob, subject=subject)

    return results
