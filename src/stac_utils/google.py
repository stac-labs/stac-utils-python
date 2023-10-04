from io import StringIO, BytesIO
import json
import logging
import os
import sys

from google.api_core.exceptions import InternalServerError, NotFound
from google.api_core.retry import if_exception_type, Retry
from google.cloud import storage, bigquery
from google.cloud.bigquery.table import Table
from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from inflection import parameterize, underscore

from .listify import listify

RETRY_EXCEPTIONS = [InternalServerError]


def get_credentials(
    service_account_blob: dict = None,
    service_account_env_name: str = "SERVICE_ACCOUNT",
    scopes: [list[str], str] = None,
    subject: str = None,
) -> [service_account.Credentials, None]:
    """Loads a Google Service Account into a Credentials object with the given scopes. Either include blob or environment name. It defaults to using the SERVICE_ACCOUNT if included in os.environ.

    :param service_account_blob: Service account blob
    :param service_account_env_name: Environmental variable name for service account
    :param scopes: Desired service account scopes
    :param subject: Service account subject
    :return: Service account credentials
    """

    if not service_account_blob:
        try:
            service_account_blob = json.loads(os.environ[service_account_env_name])
        except (json.JSONDecodeError, KeyError) as e:
            print("Service account did not load correctly")
            print(e)
            return None

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
    client_class,
    scopes: [list[str], str] = None,
    service_account_blob: dict = None,
    service_account_env_name: str = "SERVICE_ACCOUNT",
    subject: str = None,
    **kwargs,
):
    """
    Returns client of given class with given scopes

    :param client_class: Desired client class
    :param scopes: Desired scopes
    :param service_account_blob: Service account blob
    :param service_account_env_name: Environmental variable name for service account
    :param subject: Service account subject
    :return: Client of given class, scopes
    """

    if "is_auto_credential" in kwargs:
        kwargs.pop("is_auto_credential")
    credentials = get_credentials(
        scopes=scopes,
        service_account_blob=service_account_blob,
        service_account_env_name=service_account_env_name,
        subject=subject,
    )
    client = client_class(credentials=credentials, **kwargs)
    return client


def auth_gcs(scopes: list[str] = None, **kwargs) -> storage.Client:
    """
    Returns an initialized Storage client object.

    :param scopes: Desired scopes. The default scope is `cloud-platform`, but other common scopes include `gmail`, `drive`.
    :return: GCS client object
    """

    scopes = scopes or ["cloud-platform"]
    client = get_client(storage.Client, scopes, **kwargs)

    return client


def auth_bq(scopes: list[str] = None, **kwargs) -> bigquery.Client:
    """
    Returns an initialized BigQuery client object

    :param scopes: Desired scopes
    :return: BigQuery client object
    """

    scopes = scopes or ["cloud-platform", "drive"]
    client = get_client(bigquery.Client, scopes, **kwargs)

    return client


def auth_gmail(
    scopes: [list[str], str] = None,
    service_account_blob: dict = None,
    service_account_env_name: str = "SERVICE_ACCOUNT",
    subject: str = None,
    **kwargs,
) -> Resource:
    """
    Returns an initialized Gmail Client object

    :param scopes: Desired scopes. Defaults to `["gmail.labels", "gmail.modify", "gmail.readonly"]`
    :param service_account_blob: Service account blob
    :param service_account_env_name: Environmental variable name for service account
    :param subject: Service account subject
    :return: Gmail client object
    """
    return build_service(
        "gmail",
        "v1",
        ["gmail.labels", "gmail.modify", "gmail.readonly"],
        scopes=scopes,
        service_account_blob=service_account_blob,
        service_account_env_name=service_account_env_name,
        subject=subject,
        **kwargs,
    )


def make_gmail_client(*args, **kwargs) -> Resource:
    """Deprecated alias"""
    return auth_gmail(*args, **kwargs)


def auth_sheets(
    scopes: list[str] = None,
    cache_discovery: bool = False,
    service_account_blob: dict = None,
    service_account_env_name: str = "SERVICE_ACCOUNT",
    subject: str = None,
    **kwargs,
) -> Resource:
    """
    Returns an initialized Sheets client object

    :param scopes: Desired scopes, defaults to `[drive]`
    :param cache_discovery: `False` unless specified. If cache discovery is desired, set to `True`.
    :param service_account_blob: Service account blob
    :param service_account_env_name: Environmental variable name for service account
    :param subject: Service account subject
    :return: Sheets client object
    """
    return build_service(
        "sheets",
        "v4",
        ["drive"],
        scopes=scopes,
        service_account_blob=service_account_blob,
        service_account_env_name=service_account_env_name,
        subject=subject,
        **kwargs,
    )


def auth_drive(
    scopes: list[str] = None,
    cache_discovery: bool = False,
    service_account_blob: dict = None,
    service_account_env_name: str = "SERVICE_ACCOUNT",
    subject: str = None,
    **kwargs,
) -> Resource:
    """
    Returns an initialized Drive client object

    :param scopes: Desired scopes, defaults to `[drive]`
    :param cache_discovery: `False` unless specified. If cache discovery is desired, set to `True`.
    :param service_account_blob: Service account blob
    :param service_account_env_name: Environmental variable name for service account
    :param subject: Service account subject
    :return: Drive client object
    """

    return build_service(
        "drive",
        "v3",
        ["drive"],
        scopes=scopes,
        service_account_blob=service_account_blob,
        service_account_env_name=service_account_env_name,
        subject=subject,
        **kwargs,
    )


def build_service(
    service: str,
    version: str,
    default_scopes: list[str],
    scopes: list[str] = None,
    cache_discovery: bool = False,
    service_account_blob: dict = None,
    service_account_env_name: str = "SERVICE_ACCOUNT",
    subject: str = None,
    **kwargs,
) -> Resource:
    """
    Authorization for Google services, including "drive", "cloud-platform", "sheets",
    or any other service that uses build.

    :param service: "drive", "cloud-platform", "sheets", or any other service that uses build
    :param version: version of service
    :param default_scopes: default scopes for this service
    :param scopes: scopes provided by user
    :param cache_discovery: `False` unless specified. If cache discovery is desired, set to `True`.
    :param service_account_blob: Service account blob
    :param service_account_env_name: Environmental variable name for service account
    :param subject: Service account subject
    :return: client object
    """

    if "is_auto_credential" in kwargs:
        kwargs.pop("is_auto_credential")

    scopes = scopes or default_scopes
    credentials = get_credentials(
        scopes=scopes,
        service_account_blob=service_account_blob,
        service_account_env_name=service_account_env_name,
        subject=subject,
    )

    return build(
        service,
        version,
        credentials=credentials,
        cache_discovery=cache_discovery,
        **kwargs,
    )


def run_query(
    sql: str,
    client: bigquery.Client = None,
    retry_exceptions: list = None,
    job_config: bigquery.QueryJobConfig = None,
    **kwargs,
) -> list[dict]:
    """
    Performs a SQL query in BigQuery

    :param sql: SQL query to be performed
    :param client: BigQuery client
    :param retry_exceptions: Specified retry exceptions
    :param job_config: Specified query job config
    :return: Results of SQL query
    """
    client = client or auth_bq(**kwargs)

    retry_exceptions = retry_exceptions or RETRY_EXCEPTIONS
    retry_policy = Retry(predicate=if_exception_type(*retry_exceptions))

    job = client.query(sql, retry=retry_policy, job_config=job_config).result()
    results = [{k: v for k, v in row.items()} for row in job]

    return results


def get_table(table_name: str, **kwargs) -> list[dict]:
    """
    Performs a select * from the given table in BigQuery

    :param table_name: Desired table
    :return: Results of a `select all` from given table
    """

    # sadly bq's parameterized queries don't support table names
    sql = f"SELECT * FROM `{_sanitize_name(table_name)}`;"
    results = run_query(sql, **kwargs)

    return results


def create_table_from_dataframe(
    client: bigquery.Client,
    dataframe: "pd.DataFrame",
    project_name: str,
    dataset_name: str,
    table_name: str,
):
    """
    Creates a BigQuery table from Pandas dataframe

    :param client: BigQuery client
    :param dataframe: Pandas dataframe to turn into BigQuery table
    :param project_name: Desired BigQuery project name
    :param dataset_name: Desired BigQuery dataset name
    :param table_name: Desired BigQuery table name
    """

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
    """
    Gets a BigQuery table for loading given project, dataset, and table name details

    :param client: BigQuery client
    :param project_name: Specified BigQuery project name
    :param dataset_name: Specified BigQuery dataset name
    :param table_name: Specified BigQuery table name
    :return: Specified table
    """
    dataset_ref = bigquery.Dataset(project_name + "." + dataset_name)
    table_ref = dataset_ref.table(table_name)

    table = client.get_table(table_ref)

    return table


def load_data_from_dataframe(
    client: bigquery.Client,
    dataframe: "pd.DataFrame",
    project_name: str,
    dataset_name: str,
    table_name: str,
    retry_exceptions: list = None,
):
    """
    Loads data from the specified dataframe into the specified table in BigQuery

    :param client: BigQuery client
    :param dataframe: Specified Pandas dataframe
    :param project_name: Specified BigQuery project
    :param dataset_name: Specified BigQuery project name
    :param table_name: Specified BigQuery table name
    :param retry_exceptions: Desired retry exceptions
    """

    table = get_table_for_loading(client, project_name, dataset_name, table_name)
    retry_exceptions = retry_exceptions or RETRY_EXCEPTIONS
    retry_policy = Retry(predicate=if_exception_type(*retry_exceptions))
    results = client.insert_rows_from_dataframe(
        table=table,
        dataframe=dataframe,
        chunk_size=10000,
        retry=retry_policy,
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
    """
    Loads data from the specified list[dict] into the specified table in BigQuery

    :param client: BigQuery client
    :param data: List to load to table
    :param project_name: Specified BigQuery project name
    :param dataset_name: Specified BigQuery dataset name
    :param table_name: Specified BigQuery table name
    :param retry_exceptions: Desired retry exceptions
    """

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
    """
    Uploads the given file to a specified path in a GCS Bucket

    :param bucket_name: Specified GCS bucket
    :param filename: Name of file to upload
    :param destination_filename: Name for file once loaded
    :param destination_path: Desired path for file once loaded
    :param client: GCS client
    """

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
    """
    Returns the sheet data in the form of a list of lists

    :param spreadsheet_id:  Google Sheets spreadsheet ID
    :param range: Range within sheet
    :param client: Google Sheets client
    :return: List of lists of data from specified spreadsheet
    """

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
    """
    Posts the data to the Google Sheet and returns the API response

    :param data: Data to post to specified Google Sheets spreadsheet
    :param spreadsheet_id: Specified Google Sheets spreadsheet ID
    :param range: Specified range within sheet
    :param input_option: Specified input option, `RAW` by default
    :param client: Google Sheets client
    :param is_overwrite: Overwrite option, defaults to `True`
    :return: Google Sheets API response
    """

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


def text_stream_from_drive(file_id: str, client: Resource = None, **kwargs) -> StringIO:
    """
    Get csv (UTF-8 encoding) file from Google Drive and convert to a text stream.

    The csv in the drive should be shared with the email associated with the service account ideally,
    or to "anyone with the link" temporarily for this method to work.

    Use this method in conjunction with the "get_dataframe_from_text_stream" in pandas_utils to
    get a BigQuery formatted DataFrame.

    :param file_id: The alphanumeric ID for your Google Drive csv file. Must be in UTF-8 encoding
    :param client: Google Drive client
    :return: text stream
    """

    client = client or auth_drive(**kwargs)

    try:
        request = client.files().get_media(fileId=file_id)
        file = BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}.")

        stream = str(file.getvalue(), "UTF-8")
        data = StringIO(stream)

        return data

    except (HttpError, UnicodeDecodeError) as error:
        print(f"An error occurred: {error}")


def copy_file(file_id: str, new_file_name: str = None, client: Resource = None) -> str:
    client = client or auth_drive()
    new_file = client.files().copy(fileId=file_id, supportsAllDrives=True).execute()
    new_file_id = new_file["id"]
    if new_file_name:
        client.files().update(fileId=new_file_id, supportsAllDrives=True, body={"name": new_file_name}).execute()

    return new_file_id


def _sanitize_name(string: str) -> str:
    valid_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890._"

    # crudely prevent sql injection
    return "".join([s for s in string if s in valid_chars])
