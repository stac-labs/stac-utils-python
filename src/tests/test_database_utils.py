import unittest
from unittest.mock import MagicMock, patch


from src.stac_utils.database_utils import (
    make_postgres_connection,
    run_postgres_query,
    postgres_to_google_sheets,
)


class TestDatabaseUtils(unittest.TestCase):
    @patch("psycopg.connect")
    def test_make_postgres_connection(self, mock_connect: MagicMock):
        mock_pg_host = "foo.net"
        mock_pg_db = "bar"
        mock_pg_user = "spam"
        mock_pg_pw = "password"
        mock_pg_port = 5432

        make_postgres_connection(
            mock_pg_host, mock_pg_db, mock_pg_user, mock_pg_pw, mock_pg_port
        )
        mock_connect.assert_called_once_with(
            dbname=mock_pg_db,
            user=mock_pg_user,
            password=mock_pg_pw,
            host=mock_pg_host,
            port=mock_pg_port,
        )

    def test_run_postgres_query(self):
        mock_engine = MagicMock()
        mock_cursor = mock_engine.cursor.return_value.__enter__.return_value
        mock_sql_query = "foo"
        mock_data = [[0, "foo"], [1, "bar"], [2, None], [3, 42]]

        mock_cursor.fetchall.return_value = mock_data

        mock_expected_data = [["0", "foo"], ["1", "bar"], ["2", ""], ["3", "42"]]

        test_results = run_postgres_query(mock_engine, mock_sql_query)
        self.assertListEqual(mock_expected_data, test_results)
        mock_cursor.execute.assert_called_once_with(mock_sql_query)

    @patch("src.stac_utils.database_utils.make_postgres_connection")
    @patch("src.stac_utils.database_utils.run_postgres_query")
    @patch("src.stac_utils.database_utils.send_data_to_sheets")
    def test_postgres_to_google_sheets(
        self,
        mock_send_data_to_sheets: MagicMock,
        mock_run_postgres_query: MagicMock,
        mock_make_postgres_connection: MagicMock,
    ):
        mock_google_sheet_id = "1"
        mock_google_sheet_range = "a1!1"
        mock_google_sheet_headers = ["foo", "bar"]
        mock_sql_query = "spam"
        mock_data = [["0", "1"]]

        mock_engine = mock_make_postgres_connection.return_value
        mock_run_postgres_query.return_value = mock_data

        postgres_to_google_sheets(
            mock_google_sheet_id,
            mock_google_sheet_range,
            mock_google_sheet_headers,
            mock_sql_query,
        )
        mock_make_postgres_connection.assert_called_once()
        mock_run_postgres_query.assert_called_once_with(mock_engine, mock_sql_query)
        mock_send_data_to_sheets.assert_called_once_with(
            [mock_google_sheet_headers] + mock_data,
            mock_google_sheet_id,
            mock_google_sheet_range,
        )

    @patch("src.stac_utils.database_utils.make_postgres_connection")
    @patch("src.stac_utils.database_utils.run_postgres_query")
    @patch("src.stac_utils.database_utils.send_data_to_sheets")
    def test_postgres_to_google_sheets_with_engine(
        self,
        mock_send_data_to_sheets: MagicMock,
        mock_run_postgres_query: MagicMock,
        mock_make_postgres_connection: MagicMock,
    ):
        mock_google_sheet_id = "1"
        mock_google_sheet_range = "a1!1"
        mock_google_sheet_headers = ["foo", "bar"]
        mock_sql_query = "spam"
        mock_data = [["0", "1"]]

        mock_engine = MagicMock()
        mock_run_postgres_query.return_value = mock_data

        postgres_to_google_sheets(
            mock_google_sheet_id,
            mock_google_sheet_range,
            mock_google_sheet_headers,
            mock_sql_query,
            engine=mock_engine,
        )
        mock_make_postgres_connection.assert_not_called()
        mock_run_postgres_query.assert_called_once_with(mock_engine, mock_sql_query)
