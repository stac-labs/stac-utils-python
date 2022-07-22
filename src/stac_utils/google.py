import json
import os
import sys

from typing import List, Union, Mapping, Sequence

from google.cloud import storage, bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build

from . import listify


def get_credentials(
    service_account_blob: Mapping = None,
    scopes: Union[Sequence[str], str] = None,
    subject: str = None,
) -> service_account.Credentials:
    if not service_account_blob:
        try:
            service_account_blob = json.loads(os.environ["SERVICE_ACCOUNT"])
        except (json.JSONDecodeError, KeyError):
            pass

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


def auth_bq():
    scopes = ["cloud-platform"]
    credentials = get_credentials(scopes=scopes)

    client = bigquery.Client(
        credentials=credentials,
        project=credentials.project_id,
    )

    return client


def run_query(client, query_string):

    query_job = client.query(query_string)
    query_job.result()


def load_data_from_dataframe(client, dataframe, project_name, dataset_name, table_name):

    dataset_ref = bigquery.Dataset(project_name + "." + dataset_name)
    table_ref = dataset_ref.table(table_name)

    table = client.get_table(table_ref)

    print("inserting rows")

    results = client.insert_rows_from_dataframe(
        table=table, dataframe=dataframe, chunk_size=10000
    )

    print(results)


def auth_gcs():
    scopes = ["cloud-platform"]
    credentials = get_credentials(scopes=scopes)

    client = storage.Client(
        credentials=credentials,
        project=credentials.project_id,
    )

    return client


def upload_data_to_gcs(bucket_name, filename, destination_filename, destination_path):
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
    scopes = scopes or ["gmail.labels", "gmail.modify", "gmail.readonly"]

    credentials = get_credentials(service_account_blob, scopes=scopes, subject=subject)
    return build("gmail", "v1", credentials=credentials)
