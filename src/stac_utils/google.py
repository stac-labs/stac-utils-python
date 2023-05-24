import json
import logging
import os
import sys

import pandas as pd
from google.api_core.exceptions import InternalServerError
from google.api_core.retry import if_exception_type, Retry
from google.cloud import storage, bigquery
from google.cloud.bigquery.table import Table
from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource
from inflection import parameterize, underscore

from .listify import listify

RETRY_EXCEPTIONS = [InternalServerError]


def get_credentials(
    service_account_blob: dict = None,
    service_account_env_name: str = "SERVICE_ACCOUNT",
    scopes: [list[str], str] = None,
    subject: str = None,
) -> service_account.Credentials:
    """Loads a Google Service Account into a Credentials object with the given scopes"""

    if not service_account_blob:
        try:
            service_account_blob = json.loads(os.environ[service_account_env_name])
        except (json.JSONDecodeError, KeyError) as error:
            raise Exception("Service account did not load correctly", error)

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


def get_client(
    client_class, scopes: list[str], is_auto_credential: bool = False, **kwargs
):
    if is_auto_credential:
        client = client_class()
    else:
        credentials = get_credentials(scopes=scopes, **kwargs)
        client = client_class(
            credentials=credentials,
            project=credentials.project_id,
        )
    return client


def auth_gcs(scopes: list[str] = None, **kwargs) -> storage.Client:
    """Returns an initialized Storage client object"""

    scopes = scopes or ["cloud-platform"]
    client = get_client(storage.Client, scopes, **kwargs)

    return client


def auth_bq(scopes: list[str] = None, **kwargs) -> bigquery.Client:
    """Returns an initialized BigQuery client object"""

    scopes = scopes or ["cloud-platform", "drive"]
    client = get_client(bigquery.Client, scopes, **kwargs)

    return client


def auth_gmail(scopes: list[str] = None, **kwargs) -> Resource:
    """Returns an initialized Gmail Client object"""

    scopes = scopes or ["gmail.labels", "gmail.modify", "gmail.readonly"]

    credentials = get_credentials(scopes=scopes, **kwargs)
    return build("gmail", "v1", credentials=credentials)


def make_gmail_client(*args, **kwargs) -> Resource:
    """ Deprecated alias """
    return auth_gmail(*args, **kwargs)


def auth_sheets(scopes: list[str] = None, **kwargs) -> Resource:
    """Returns an initialized Sheets client object"""

    scopes = scopes or ["drive"]
    credentials = get_credentials(scopes=scopes, **kwargs)

    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


def run_query(
    sql: str,
    client: bigquery.Client = None,
    retry_exceptions: list = None,
    job_config: bigquery.QueryJobConfig = None,
    **kwargs,
) -> list[dict]:
    """Performs a SQL query in BigQuery"""
    client = client or auth_bq(**kwargs)

    retry_exceptions = retry_exceptions or RETRY_EXCEPTIONS
    retry_policy = Retry(predicate=if_exception_type(*retry_exceptions))

    job = client.query(sql, retry=retry_policy, job_config=job_config).result()
    results = [{k: v for k, v in row.items()} for row in job]

    return results


def get_table(table_name: str, **kwargs) -> list[dict]:
    """Performs a select * from the given table in BigQuery"""

    # sadly bq's parameterized queries don't support table names
    sql = f"SELECT * FROM `{_sanitize_name(table_name)}`;"
    results = run_query(sql, **kwargs)

    return results


def create_table_from_dataframe(
    client: bigquery.Client,
    dataframe: pd.DataFrame,
    project_name: str,
    dataset_name: str,
    table_name: str,
):
    column_name_conversion = {}
    column_definitions = []
    for column_index in range(len(dataframe.columns)):
        column_name = dataframe.columns[column_index]
        db_column_name = underscore(parameterize(column_name))
        column_name_conversion[column_name] = db_column_name
        datatype = dataframe.dtypes[column_index].name
        if datatype == "object":
            column_definitions.append(f"{db_column_name} STRING")
        elif datatype == "int64":
            column_definitions.append(f"{db_column_name} INT64")
        elif datatype == "float64":
            column_definitions.append(f"{db_column_name} NUMERIC")
        else:
            raise ValueError(f"Unknown data type {datatype} on column {column_name}")

    dataframe = dataframe.rename(columns=column_name_conversion)
    table_definition_sql = f"""
        DROP TABLE IF EXISTS 
            {project_name}.{dataset_name}.{table_name} 
        ;
        CREATE TABLE {project_name}.{dataset_name}.{table_name} ( 
            {", ".join(column_definitions)}
        );
    """
    print(table_definition_sql)
    run_query(table_definition_sql, client=client)
    load_data_from_dataframe(client, dataframe, project_name, dataset_name, table_name)


def get_table_for_loading(
    client: bigquery.Client,
    project_name: str,
    dataset_name: str,
    table_name: str,
) -> Table:
    dataset_ref = bigquery.Dataset(project_name + "." + dataset_name)
    table_ref = dataset_ref.table(table_name)

    table = client.get_table(table_ref)

    return table


def load_data_from_dataframe(
    client: bigquery.Client,
    dataframe: pd.DataFrame,
    project_name: str,
    dataset_name: str,
    table_name: str,
    retry_exceptions: list = None,
):
    """Loads data from the specified dataframe into the specified table in BigQuery"""

    table = get_table_for_loading(client, project_name, dataset_name, table_name)
    retry_exceptions = retry_exceptions or RETRY_EXCEPTIONS
    retry_policy = Retry(predicate=if_exception_type(*retry_exceptions))
    results = client.insert_rows_from_dataframe(
        table=table, dataframe=dataframe, chunk_size=10000, retry=retry_policy,
    )

    logging.info(f"inserted {len(results)} rows")


def load_data_from_list(
    client: bigquery.Client,
    data: list[dict],
    project_name: str,
    dataset_name: str,
    table_name: str,
    retry_exceptions: list = None,
):
    """Loads data from the specified list[dict] into the specified table in BigQuery"""

    table = get_table_for_loading(client, project_name, dataset_name, table_name)
    retry_exceptions = retry_exceptions or RETRY_EXCEPTIONS
    retry_policy = Retry(predicate=if_exception_type(*retry_exceptions))
    results = client.insert_rows(table=table, rows=data, retry=retry_policy)

    logging.info(f"inserted {len(results)} rows")


def upload_data_to_gcs(
    bucket_name: str,
    filename: str,
    destination_filename: str,
    destination_path: str,
    client: storage.Client = None,
    **kwargs,
):
    """Uploads the given file to a specified path in a GCS Bucket"""

    destination_path = destination_path.strip("/")
    destination_blob_name = destination_path + "/" + destination_filename

    client = client or auth_gcs(**kwargs)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    if not blob.exists(client):
        print(f"Uploading {filename} to {bucket_name}")
        blob.chunk_size = 5 * 1024 * 1024
        blob.upload_from_filename(filename)

        print("File", filename, "uploaded to GCS as", destination_blob_name)
    else:
        print("Already on GCS", file=sys.stderr)


def get_data_from_sheets(
    spreadsheet_id: str, range: str, client: Resource = None, **kwargs
) -> list[list]:
    """Returns the sheet data in the form of a list of lists"""

    client = client or auth_sheets(**kwargs)

    request = (
        client.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range)
    )
    response = request.execute()
    return response.get("values")


def send_data_to_sheets(
    data: list[list],
    spreadsheet_id: str,
    range: str,
    input_option: str = "RAW",
    client: Resource = None,
    is_overwrite: bool = True,
    **kwargs,
) -> dict:
    """Posts the data to the Google Sheet and returns the API response"""

    client = client or auth_sheets(**kwargs)

    sheet_modifier = client.spreadsheets().values()

    if is_overwrite:
        request = sheet_modifier.update(
            spreadsheetId=spreadsheet_id,
            range=range,
            valueInputOption=input_option,
            body={"values": data},
        )
    else:
        request = sheet_modifier.append(
            spreadsheetId=spreadsheet_id,
            range=range,
            valueInputOption=input_option,
            body={"values": data},
        )
    response = request.execute()
    return response


def _sanitize_name(string: str) -> str:
    valid_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890._"

    # crudely prevent sql injection
    return "".join([s for s in string if s in valid_chars])
