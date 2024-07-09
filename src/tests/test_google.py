import os
import unittest
from unittest.mock import MagicMock, patch

from io import StringIO, BytesIO

import pandas as pd
from google.cloud import storage, bigquery
from googleapiclient.errors import HttpError


from src.stac_utils.google import (
    get_credentials,
    get_client,
    auth_bq,
    auth_gcs,
    auth_gmail,
    auth_sheets,
    auth_drive,
    build_service,
    make_gmail_client,
    run_query,
    get_table,
    create_table_from_dataframe,
    get_table_for_loading,
    load_data_from_dataframe,
    load_data_from_list,
    upload_data_to_gcs,
    get_data_from_sheets,
    send_data_to_sheets,
    copy_file,
    _sanitize_name,
    text_stream_from_drive,
)


class TestGoogle(unittest.TestCase):
    @patch("src.stac_utils.google.service_account")
    def test_get_credentials_json_blob(self, mock_service_account: MagicMock):
        """Test credentials are created successfully from blob"""

        mock_blob = {"FOO": "BAR"}
        get_credentials(mock_blob, scopes="foo")
        mock_service_account.Credentials.from_service_account_info.assert_called_once_with(
            mock_blob,
            scopes=["https://www.googleapis.com/auth/foo"],
            subject=None,
        )

    @patch("src.stac_utils.google.service_account")
    def test_get_credentials_environment(self, mock_service_account: MagicMock):
        """Test credentials are created successfully from environment"""

        mock_environ = {"SERVICE_ACCOUNT": """{"FOO": "BAR"}"""}
        with patch.dict(os.environ, values=mock_environ):
            get_credentials(scopes="foo")
            mock_service_account.Credentials.from_service_account_info.assert_called_once_with(
                {"FOO": "BAR"},
                scopes=["https://www.googleapis.com/auth/foo"],
                subject=None,
            )

    def test_get_credentials_missing(self):
        """Test credentials returns None because no credentials were provided"""

        self.assertIsNone(get_credentials(scopes="foo"))

    @patch("src.stac_utils.google.get_credentials")
    def test_get_client(self, mock_get_credentials: MagicMock):
        """Test it gets credentials and makes a client"""

        mock_client_class = MagicMock()
        result_client = get_client(mock_client_class, ["foo"], bar=True)
        mock_get_credentials.assert_called_once_with(
            scopes=["foo"],
            service_account_blob=None,
            service_account_env_name="SERVICE_ACCOUNT",
            subject=None,
        )
        mock_client_class.assert_called_once_with(
            credentials=mock_get_credentials.return_value, bar=True
        )
        self.assertIs(mock_client_class.return_value, result_client)

    @patch("src.stac_utils.google.get_credentials")
    def test_get_client_default_credential(self, mock_get_credentials: MagicMock):
        """Test it creates a client from default credentials"""

        mock_client_class = MagicMock()
        mock_get_credentials.return_value = None

        result_client = get_client(mock_client_class, ["foo"])
        mock_get_credentials.assert_called_once_with(
            scopes=["foo"],
            service_account_blob=None,
            service_account_env_name="SERVICE_ACCOUNT",
            subject=None,
        )
        mock_client_class.assert_called_once_with(
            credentials=None,
        )
        self.assertIs(mock_client_class.return_value, result_client)

    @patch("src.stac_utils.google.get_client")
    def test_auth_gcs(self, mock_get_client: MagicMock):
        """Test it makes a gcs client"""

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result_client = auth_gcs()

        mock_get_client.assert_called_once_with(storage.Client, ["cloud-platform"])
        self.assertIs(mock_client, result_client)

    @patch("src.stac_utils.google.get_client")
    def test_auth_gcs_other_scopes(self, mock_get_client: MagicMock):
        """Test auth gcs with custom scopes"""

        auth_gcs(["foo", "bar"])

        mock_get_client.assert_called_once_with(storage.Client, ["foo", "bar"])

    @patch("src.stac_utils.google.get_client")
    def test_auth_bq(self, mock_get_client: MagicMock):
        """Test it makes a bigquery client"""

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result_client = auth_bq()

        mock_get_client.assert_called_once_with(
            bigquery.Client, ["cloud-platform", "drive"]
        )
        self.assertIs(mock_client, result_client)

    @patch("src.stac_utils.google.get_client")
    def test_auth_bq_other_scopes(self, mock_get_client: MagicMock):
        """Test auth bq with custom scopes"""

        auth_bq(["foo", "bar"])

        mock_get_client.assert_called_once_with(bigquery.Client, ["foo", "bar"])

    @patch("src.stac_utils.google.build_service")
    def test_auth_gmail(self, mock_build_service: MagicMock):
        """Test it gets credentials & builds a gmail client"""

        auth_gmail()

        mock_build_service.assert_called_once_with(
            "gmail",
            "v1",
            ["gmail.labels", "gmail.modify", "gmail.readonly"],
            scopes=None,
            service_account_blob=None,
            service_account_env_name="SERVICE_ACCOUNT",
            subject=None,
        )

    @patch("src.stac_utils.google.auth_gmail")
    def test_make_gmail_client(self, mock_auth_gmail: MagicMock):
        """Test it simply calls auth_gmail"""

        make_gmail_client("foo", bar="spam")
        mock_auth_gmail.assert_called_once_with("foo", bar="spam")

    @patch("src.stac_utils.google.build_service")
    def test_auth_sheets(self, mock_build_service: MagicMock):
        """Test it gets credentials & builds a gmail client"""

        auth_sheets()

        mock_build_service.assert_called_once_with(
            "sheets",
            "v4",
            ["drive"],
            scopes=None,
            service_account_blob=None,
            service_account_env_name="SERVICE_ACCOUNT",
            subject=None,
        )

    @patch("src.stac_utils.google.build_service")
    def test_auth_drive(self, mock_build_service: MagicMock):
        """Test it gets credentials & builds a gmail client"""

        auth_drive()

        mock_build_service.assert_called_once_with(
            "drive",
            "v3",
            ["drive"],
            scopes=None,
            service_account_blob=None,
            service_account_env_name="SERVICE_ACCOUNT",
            subject=None,
        )

    @patch("src.stac_utils.google.build")
    @patch("src.stac_utils.google.get_credentials")
    def test_build_service(
        self, mock_get_credentials: MagicMock, mock_build: MagicMock
    ):
        """Test it gets credentials & builds a sheets client"""

        mock_credentials = MagicMock()
        mock_get_credentials.return_value = mock_credentials

        build_service("foo", "v1", ["bar"])

        mock_get_credentials.assert_called_once_with(
            scopes=["bar"],
            service_account_blob=None,
            service_account_env_name="SERVICE_ACCOUNT",
            subject=None,
        )

        mock_build.assert_called_once_with(
            "foo", "v1", credentials=mock_credentials, cache_discovery=False
        )

    @patch("src.stac_utils.google.build")
    @patch("src.stac_utils.google.get_credentials")
    def test_build_service_other_scopes(
        self, mock_get_credentials: MagicMock, mock_build: MagicMock
    ):
        """Test it gets credentials & builds a sheets client"""

        mock_credentials = MagicMock()
        mock_get_credentials.return_value = mock_credentials

        build_service("foo", "v1", ["bar"], scopes=["spam"])

        mock_get_credentials.assert_called_once_with(
            scopes=["spam"],
            service_account_blob=None,
            service_account_env_name="SERVICE_ACCOUNT",
            subject=None,
        )

        mock_build.assert_called_once_with(
            "foo", "v1", credentials=mock_credentials, cache_discovery=False
        )

    @patch("src.stac_utils.google.Retry")
    @patch("src.stac_utils.google.auth_bq")
    def test_run_query_provided_client(
        self, mock_auth_bq: MagicMock, mock_retry: MagicMock
    ):
        """Test run query with provided client"""

        mock_client = MagicMock()
        mock_query_job = MagicMock()
        mock_client.query = MagicMock(return_value=mock_query_job)

        mock_job = [{"foo": "bar"}]
        mock_query_job.result = MagicMock(return_value=mock_job)

        mock_job_config = MagicMock()
        mock_retry_policy = MagicMock()
        mock_retry.return_value = mock_retry_policy

        test_sql = "SELECT * FROM foo.bar;"
        test_results = run_query(
            test_sql,
            client=mock_client,
            job_config=mock_job_config,
            spam=True,
        )
        mock_auth_bq.assert_not_called()
        mock_client.query.assert_called_once_with(
            test_sql,
            retry=mock_retry_policy,
            job_config=mock_job_config,
        )
        mock_query_job.result.assert_called_once()
        self.assertEqual(mock_job, test_results)

    @patch("src.stac_utils.google.auth_bq")
    def test_run_query_no_client(self, mock_auth_bq: MagicMock):
        """Test run query with no client"""

        mock_client = MagicMock()
        mock_auth_bq.return_value = mock_client
        mock_client.query = MagicMock()

        run_query("", spam=True)
        mock_auth_bq.assert_called_once_with(spam=True)
        mock_client.query.assert_called_once()

    @patch("src.stac_utils.google.run_query")
    def test_get_table(self, mock_run_query: MagicMock):
        """Test get table"""

        mock_results = MagicMock()
        mock_run_query.return_value = mock_results

        test_results = get_table("foo.bar", spam=True)
        mock_run_query.assert_called_once_with("SELECT * FROM `foo.bar`;", spam=True)
        self.assertIs(mock_results, test_results)

    @patch("src.stac_utils.google.run_query")
    @patch("src.stac_utils.google.load_data_from_dataframe")
    def test_create_table_from_dataframe(
        self, mock_load_data: MagicMock, mock_run_query: MagicMock
    ):
        """Test create table from dataframe"""

        mock_df = pd.DataFrame([{"foo": 1, "bar": 2.5, "spam": "spam", "baz": False}])

        table_definition_sql = f"""
        DROP TABLE IF EXISTS 
            foo.bar.spam 
        ;
        CREATE TABLE foo.bar.spam ( 
            foo INT64, bar NUMERIC, spam STRING, baz BOOL
        );
    """

        mock_client = MagicMock()
        create_table_from_dataframe(
            mock_client,
            mock_df,
            project_name="foo",
            dataset_name="bar",
            table_name="spam",
        )
        mock_run_query.assert_called_once_with(table_definition_sql, client=mock_client)
        mock_load_data.assert_called_once()

    @patch("src.stac_utils.google.run_query")
    @patch("src.stac_utils.google.load_data_from_dataframe")
    def test_create_table_from_dataframe_bad_types(
        self, mock_load_data: MagicMock, mock_run_query: MagicMock
    ):
        """Test create table from dataframe with bad type"""

        mock_df = pd.DataFrame(
            [{"foo": pd.Timestamp("20230524"), "bar": 2.5, "spam": "spam"}]
        )

        mock_client = MagicMock()
        self.assertRaises(
            ValueError,
            create_table_from_dataframe,
            mock_client,
            mock_df,
            project_name="foo",
            dataset_name="bar",
            table_name="spam",
        )
        mock_run_query.assert_not_called()
        mock_load_data.assert_not_called()

    @patch("src.stac_utils.google.bigquery")
    def test_get_table_for_loading(self, mock_bigquery: MagicMock):
        """Test get table for loading"""
        mock_client = MagicMock()
        get_table_for_loading(mock_client, "foo", "bar", "spam")
        mock_bigquery.Dataset.assert_called_once_with("foo.bar")
        mock_client.get_table.assert_called_once()

    @patch("src.stac_utils.google.get_table_for_loading")
    def test_load_data_from_dataframe(self, mock_get_table: MagicMock):
        """Test load data from dataframe"""
        mock_client = MagicMock()
        load_data_from_dataframe(mock_client, pd.DataFrame(), "foo", "bar", "spam")
        mock_get_table.assert_called_once_with(mock_client, "foo", "bar", "spam")
        mock_client.insert_rows_from_dataframe.assert_called_once()

    @patch("src.stac_utils.google.get_table_for_loading")
    def test_load_data_from_list(self, mock_get_table: MagicMock):
        """Test load data from list"""
        mock_client = MagicMock()
        load_data_from_list(mock_client, [], "foo", "bar", "spam")
        mock_get_table.assert_called_once_with(mock_client, "foo", "bar", "spam")
        mock_client.insert_rows.assert_called_once()

    @patch("src.stac_utils.google.auth_gcs")
    def test_upload_data_to_gcs(self, mock_auth_gcs: MagicMock):
        """Test upload data to gcs"""
        mock_client = MagicMock()
        mock_auth_gcs.return_value = mock_client
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = False
        upload_data_to_gcs("foo", "bar", "spam", "eggs")
        mock_auth_gcs.assert_called_once()
        mock_client.bucket.assert_called_once_with("foo")
        mock_bucket.blob.assert_called_once_with("eggs/spam")
        mock_blob.upload_from_filename.assert_called_once_with("bar")

    @patch("src.stac_utils.google.auth_gcs")
    def test_upload_data_to_gcs_with_provided_client(self, mock_auth_gcs: MagicMock):
        """Test upload data to gcs with provided client"""
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = False
        upload_data_to_gcs("foo", "bar", "spam", "eggs", client=mock_client)
        mock_auth_gcs.assert_not_called()
        mock_blob.upload_from_filename.assert_called_once_with("bar")

    @patch("src.stac_utils.google.auth_gcs")
    def test_upload_data_to_gcs_already_exists(self, mock_auth_gcs: MagicMock):
        """Test upload data to gcs when file already exists"""
        mock_client = MagicMock()
        mock_auth_gcs.return_value = mock_client
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True
        upload_data_to_gcs("foo", "bar", "spam", "eggs")
        mock_blob.upload_from_filename.assert_not_called()

    @patch("src.stac_utils.google.auth_sheets")
    def test_get_data_from_sheets(self, mock_auth_sheets: MagicMock):
        """Test get data from sheets"""
        mock_client = MagicMock()
        mock_auth_sheets.return_value = mock_client
        get_data_from_sheets("foo", "bar")
        mock_client.spreadsheets.return_value.values.return_value.get.assert_called_once_with(
            spreadsheetId="foo", range="bar"
        )

    @patch("src.stac_utils.google.auth_sheets")
    def test_get_data_from_sheets_provided_client(self, mock_auth_sheets: MagicMock):
        """Test get data from sheets with client provided"""
        mock_client = MagicMock()
        get_data_from_sheets("foo", "bar", client=mock_client)
        mock_auth_sheets.assert_not_called()

    @patch("src.stac_utils.google.auth_sheets")
    def test_send_data_to_sheets_overwrite(self, mock_auth_sheets: MagicMock):
        """test send to sheets with overwrite"""
        mock_client = MagicMock()
        mock_auth_sheets.return_value = mock_client
        mock_modifier = MagicMock()
        mock_client.spreadsheets.return_value.values.return_value = mock_modifier
        send_data_to_sheets([[]], "foo", "bar")
        mock_modifier.append.assert_not_called()
        mock_modifier.update.assert_called_once_with(
            spreadsheetId="foo",
            range="bar",
            valueInputOption="RAW",
            body={"values": [[]]},
        )

    @patch("src.stac_utils.google.auth_sheets")
    def test_send_data_to_sheets_no_overwrite(self, mock_auth_sheets: MagicMock):
        """test send to sheets with no overwrite"""
        mock_client = MagicMock()
        mock_auth_sheets.return_value = mock_client
        mock_modifier = MagicMock()
        mock_client.spreadsheets.return_value.values.return_value = mock_modifier
        send_data_to_sheets([[]], "foo", "bar", is_overwrite=False)
        mock_modifier.update.assert_not_called()
        mock_modifier.append.assert_called_once_with(
            spreadsheetId="foo",
            range="bar",
            valueInputOption="RAW",
            body={"values": [[]]},
        )

    @patch("src.stac_utils.google.auth_sheets")
    def test_send_data_to_sheets_with_client(self, mock_auth_sheets: MagicMock):
        """test send to sheets with client"""
        mock_client = MagicMock()
        send_data_to_sheets([[]], "foo", "bar", is_overwrite=False, client=mock_client)
        mock_auth_sheets.assert_not_called()

    @patch("src.stac_utils.google.auth_sheets")
    def test_send_data_to_sheets_with_null_overwrite(self, mock_auth_sheets: MagicMock):
        """test send to sheets with null overwrite"""
        mock_client = MagicMock()
        mock_auth_sheets.return_value = mock_client
        mock_modifier = MagicMock()
        mock_client.spreadsheets.return_value.values.return_value = mock_modifier
        send_data_to_sheets(
            [[1, None, 2], [3, 4, 5]], "foo", "bar", is_fill_in_nulls=True
        )
        mock_modifier.append.assert_not_called()
        mock_modifier.update.assert_called_once_with(
            spreadsheetId="foo",
            range="bar",
            valueInputOption="RAW",
            body={"values": [[1, "", 2], [3, 4, 5]]},
        )

    def test__sanitize_name(self):
        """Test sanitize name"""

        self.assertEqual(_sanitize_name("Foo.Bar"), "Foo.Bar")
        self.assertEqual(_sanitize_name("foo.bar"), "foo.bar")
        self.assertEqual(_sanitize_name("FOO.BAR"), "FOO.BAR")
        self.assertEqual(_sanitize_name("Foo1.Bar2"), "Foo1.Bar2")
        self.assertEqual(_sanitize_name("Foo_1.Bar_2"), "Foo_1.Bar_2")
        self.assertEqual(_sanitize_name("foo;DROP TABLE.bar"), "fooDROPTABLE.bar")
        self.assertEqual(_sanitize_name("foo???.bar"), "foo.bar")
        self.assertEqual(_sanitize_name("'foo'.'bar'"), "foo.bar")

    @patch("src.stac_utils.google.MediaIoBaseDownload")
    @patch("src.stac_utils.google.auth_drive")
    def test_text_stream_from_drive_with_client(
        self, mock_auth_drive: MagicMock, mock_media_download: MagicMock
    ):
        """Test text stream from drive"""
        # client
        mock_client = MagicMock()

        # request
        mock_request = MagicMock()
        mock_client.files.return_value.get_media.return_value = mock_request

        # downloader
        mock_downloader = MagicMock()
        mock_media_download.return_value = mock_downloader

        # handle next_chunk iterable initial case
        mock_download_progress = MagicMock()

        # handle next_chunk iterable final case
        mock_download_complete = MagicMock(progress=lambda: 1)

        # downloader start case (at 1)
        mock_downloader.next_chunk.return_value[0].progress.return_value = (
            mock_download_progress
        )

        # side effect to handle downloader range
        # ("if side_effect is an iterable then each call to the mock will return the next value from the iterable")
        mock_downloader.next_chunk.side_effect = [
            (mock_download_progress, False),
            (mock_download_complete, True),
        ]
        # function call
        data = text_stream_from_drive("foo", client=mock_client)

        # assert no repeated calls to  mock_client
        mock_auth_drive.assert_not_called()

        # assert get_media called with mock fileID
        mock_client.files.return_value.get_media.assert_called_once_with(fileId="foo")

        # assert the file input in mock_media_download is BytesIO
        self.assertIsInstance(mock_media_download.call_args.args[0], BytesIO)

        # assert the request input in MediaIoBaseDownload is equal to mock_request
        self.assertEqual(mock_media_download.call_args.args[1], mock_request)

        # assert mock_media_download is called once, to create downloader
        mock_media_download.assert_called_once()

        # assert downloader called twice
        self.assertEqual(mock_downloader.next_chunk.call_count, 2)

        # assert function output is StringIO type
        self.assertIsInstance(data, StringIO)

    def test_text_stream_from_drive_http_errors(
        self,
    ):
        """Test text stream from drive"""

        mock_client = MagicMock()
        mock_client.files.return_value.get_media.side_effect = HttpError(
            MagicMock(), b""
        )

        # http error test
        text_stream_from_drive(client=mock_client, file_id="foo")

    def test_text_stream_from_drive_unicode_errors(
        self,
    ):
        """Test text stream from drive"""

        mock_client = MagicMock()
        mock_client.files.return_value.get_media.side_effect = UnicodeDecodeError(
            "Testing", b"spam", MagicMock(), MagicMock(), "Foo"
        )

        # http error test
        text_stream_from_drive(client=mock_client, file_id="foo")

    @patch("src.stac_utils.google.auth_drive")
    def test_copy_file_no_client(self, mock_auth_drive: MagicMock):
        mock_client = MagicMock()
        mock_auth_drive.return_value = mock_client
        mock_file_id = MagicMock()

        copy_file(mock_file_id)
        mock_auth_drive.assert_called_once()
        mock_client.files.return_value.copy.return_value.execute.assert_called_once()
        mock_client.files.return_value.update.return_value.execute.assert_not_called()

    @patch("src.stac_utils.google.auth_drive")
    def test_copy_file_provided_client(self, mock_auth_drive: MagicMock):
        mock_client = MagicMock()
        mock_file_id = MagicMock()

        copy_file(mock_file_id, client=mock_client)
        mock_auth_drive.assert_not_called()
        mock_client.files.return_value.copy.return_value.execute.assert_called_once()
        mock_client.files.return_value.update.return_value.execute.assert_not_called()

    @patch("src.stac_utils.google.auth_drive")
    def test_copy_file_new_file_name(self, mock_auth_drive: MagicMock):
        mock_client = MagicMock()
        mock_auth_drive.return_value = mock_client
        mock_file_id = MagicMock()
        mock_new_file_name = "foo"

        copy_file(mock_file_id, mock_new_file_name)
        mock_auth_drive.assert_called_once()
        mock_client.files.return_value.copy.return_value.execute.assert_called_once()
        mock_client.files.return_value.update.return_value.execute.assert_called_once()


if __name__ == "__main__":
    unittest.main()
