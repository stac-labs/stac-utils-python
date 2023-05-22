import unittest
from unittest.mock import MagicMock, patch, call

from google.cloud import storage, bigquery
from googleapiclient.discovery import Resource

from src.stac_utils.google import (
    get_credentials,
    get_client,
    auth_bq,
    auth_gcs,
    auth_gmail,
    auth_sheets,
    make_gmail_client,
    run_query,
    get_table,
    create_table_from_dataframe,
    load_data_from_dataframe,
    upload_data_to_gcs,
    get_data_from_sheets,
    send_data_to_sheets,
    _sanitize_name,
)


class TestGoogle(unittest.TestCase):
    def test_get_credentials_json_blob(self):
        """Test credentials are created successfully from blob"""

    def test_get_credentials_environment(self):
        """Test credentials are created successfully from environment"""

    def test_get_credentials_missing(self):
        """Test credentials fails because no credentials were provided"""

    @patch("src.stac_utils.google.get_credentials")
    def test_get_client(self, mock_get_credentials: MagicMock):
        """Test it gets credentials and makes a client"""

        mock_client = MagicMock()
        mock_client_class = MagicMock(
            return_value=mock_client
        )
        mock_credentials = MagicMock()
        mock_credentials.project_id = 42
        mock_get_credentials.return_value = mock_credentials

        result_client = get_client(mock_client_class, ["foo"], bar=True)
        mock_get_credentials.assert_called_once_with(scopes=["foo"], bar=True)
        mock_client_class.assert_called_once_with(
            credentials=mock_credentials,
            project=mock_credentials.project_id,
        )
        self.assertIs(result_client, mock_client)

    @patch("src.stac_utils.google.get_credentials")
    def test_get_client_auto_credential(self, mock_get_credentials: MagicMock):
        """Test it creates a client from default credentials"""

        mock_client = MagicMock()
        mock_client_class = MagicMock(
            return_value=mock_client
        )

        result_client = get_client(mock_client_class, ["foo"], is_auto_credential=True)
        mock_get_credentials.assert_not_called()
        mock_client_class.assert_called_once_with()
        self.assertIs(result_client, mock_client)

    @patch("src.stac_utils.google.get_client")
    def test_auth_gcs(self, mock_get_client: MagicMock):
        """Test it makes a gcs client"""

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result_client = auth_gcs()

        mock_get_client.assert_called_once_with(
            storage.Client, ["cloud-platform"]
        )
        self.assertIs(result_client, mock_client)

    @patch("src.stac_utils.google.get_client")
    def test_auth_gcs_other_scopes(self, mock_get_client: MagicMock):
        """Test auth gcs with custom scopes"""

        auth_gcs(["foo", "bar"])

        mock_get_client.assert_called_once_with(
            storage.Client, ["foo", "bar"]
        )

    @patch("src.stac_utils.google.get_client")
    def test_auth_bq(self, mock_get_client: MagicMock):
        """Test it makes a bigquery client"""

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result_client = auth_bq()

        mock_get_client.assert_called_once_with(
            bigquery.Client, ["cloud-platform", "drive"]
        )
        self.assertIs(result_client, mock_client)

    @patch("src.stac_utils.google.get_client")
    def test_auth_bq_other_scopes(self, mock_get_client: MagicMock):
        """Test auth bq with custom scopes"""

        auth_bq(["foo", "bar"])

        mock_get_client.assert_called_once_with(
            bigquery.Client, ["foo", "bar"]
        )

    @patch("src.stac_utils.google.get_credentials")
    def test_auth_gmail(self, mock_get_credentials: MagicMock):
        """Test it gets credentials & builds a gmail client"""

        mock_credentials = MagicMock()
        mock_get_credentials.return_value = mock_credentials

        result_client = auth_gmail()

        mock_get_credentials.assert_called_once_with(
            scopes=["gmail.labels", "gmail.modify", "gmail.readonly"]
        )
        self.assertIsInstance(result_client, Resource)

    @patch("src.stac_utils.google.get_credentials")
    def test_auth_gmail_other_scopes(self, mock_get_credentials: MagicMock):
        """Test auth gmail with custom scopes"""

        mock_credentials = MagicMock()
        mock_get_credentials.return_value = mock_credentials

        auth_gmail(["foo", "bar"])

        mock_get_credentials.assert_called_once_with(
            scopes=["foo", "bar"]
        )

    @patch("src.stac_utils.google.auth_gmail")
    def test_make_gmail_client(self, mock_auth_gmail: MagicMock):
        """Test it simply calls auth_gmail """

        make_gmail_client("foo", bar="spam")
        mock_auth_gmail.assert_called_once_with("foo", bar="spam")

    @patch("src.stac_utils.google.get_credentials")
    def test_auth_sheets(self, mock_get_credentials: MagicMock):
        """Test it gets credentials & builds a sheets client"""

        mock_credentials = MagicMock()
        mock_get_credentials.return_value = mock_credentials

        result_client = auth_sheets()

        mock_get_credentials.assert_called_once_with(
            scopes=["drive"]
        )
        self.assertIsInstance(result_client, Resource)

    @patch("src.stac_utils.google.get_credentials")
    def test_auth_sheets_other_scopes(self, mock_get_credentials: MagicMock):
        """Test auth sheets with custom scopes"""

        mock_credentials = MagicMock()
        mock_get_credentials.return_value = mock_credentials

        auth_sheets(["foo", "bar"])

        mock_get_credentials.assert_called_once_with(
            scopes=["foo", "bar"]
        )

    def test_run_query_provided_client(self):
        """Test run query with provided client"""

    def test_run_query_no_client(self):
        """Test run query with no client"""

    @patch("src.stac_utils.google.run_query")
    def test_get_table(self, mock_run_query: MagicMock):
        """Test get table"""

        mock_results = MagicMock()
        mock_run_query.return_value = mock_results

        test_results = get_table("foo.bar", spam=True)
        mock_run_query.assert_called_once_with(
            "SELECT * FROM `foo.bar`;", spam=True
        )
        self.assertIs(test_results, mock_results)

    def test_create_table_from_dataframe(self):
        """Test create table from dataframe"""

    def test_create_table_from_dataframe_bad_types(self):
        """Test create table from dataframe with bad type"""

    def test_get_table_for_loading(self):
        """Test get table for loading"""

    def test_load_data_from_dataframe(self):
        """Test load data from dataframe"""

    def test_load_data_from_list(self):
        """Test load data from list"""

    def test_upload_data_to_gcs(self):
        """Test upload data to gcs"""

    def test_upload_data_to_gcs_already_exists(self):
        """Test upload data to gcs when file already exists"""

    def test_get_data_from_sheets(self):
        """Test get data from sheest"""

    def test_get_data_from_sheets_no_client(self):
        """Test get data from sheets with no client provided"""

    def test_send_data_to_sheets_no_overwrite(self):
        """test send to sheets with no overwrite"""

    def test_send_data_to_sheets_overwrite(self):
        """test send to sheets with overwrite"""

    def test_send_data_to_sheets_no_client(self):
        """test send to sheets with no client and no overwrite"""

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


if __name__ == "__main__":
    unittest.main()
