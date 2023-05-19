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
    def test_get_credentials(self):
        """Test credentials are created successfully"""

    def test_get_credentials_environment(self):
        """Test credentials are created successfully from environment"""

    def test_get_credentials_missing(self):
        """Test credentials fails because no credentials were provided"""

    def test_auth_bq(self):
        """Test it gets credentials and makes a client"""

    def test_run_query_provided_client(self):
        """Test run query with provided client"""

    def test_get_table(self):
        """Test get table"""

    def test_get_table_environment_blob(self):
        """Test loading service account blob from environment"""

    def test_create_table_from_dataframe(self):
        """Test create table from dataframe"""

    def test_create_table_from_dataframe_bad_types(self):
        """Test create table from dataframe with bad type"""

    def test_load_data_from_dataframe(self):
        """Test load data from dataframe"""

    def test_auth_gcs(self):
        """Test auth gcs"""

    def test_upload_data_to_gcs(self):
        """Test upload data to gcs"""

    def test_upload_data_to_gcs_already_exists(self):
        """Test upload data to gcs"""

    def test_make_gmail_client(self):
        """Test make gmail client"""

    def test_make_gmail_client_other_scopes(self):
        """Test make gmail client with custom scopes"""

    def test_auth_sheets(self):
        """Test auth sheets"""

    def test_auth_sheets_other_scopes(self):
        """Test auth sheets with custom scopes"""

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


if __name__ == "__main__":
    unittest.main()
