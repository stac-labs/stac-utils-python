import unittest

from src.stac_utils.google import (
    get_credentials,
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

    def test_get_client(self):
        """Test it gets credentials and makes a client"""

    def test_get_client_auto_credential(self):
        """Test it creates a client from default credentials"""

    def test_auth_gcs(self):
        """Test it makes a gcs client"""

    def test_auth_gcs_other_scopes(self):
        """Test auth gcs with custom scopes"""

    def test_auth_bq(self):
        """Test it makes a bigquery client"""

    def test_auth_bq_other_scopes(self):
        """Test auth bq with custom scopes"""

    def test_auth_gmail(self):
        """Test it gets credentials & builds a gmail client"""

    def test_auth_gmail_other_scopes(self):
        """Test auth gmail with custom scopes"""

    def test_make_gmail_client(self):
        """Test it simply calls auth_gmail """

    def test_auth_sheets(self):
        """Test it gets credentials & builds a sheets client"""

    def test_auth_sheets_other_scopes(self):
        """Test auth sheets with custom scopes"""

    def test_run_query_provided_client(self):
        """Test run query with provided client"""

    def test_run_query_no_client(self):
        """Test run query with no client"""

    def test_get_table(self):
        """Test get table"""

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
