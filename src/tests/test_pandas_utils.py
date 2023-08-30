import unittest
from unittest.mock import MagicMock, patch
from io import StringIO
import pandas as pd

from src.stac_utils.pandas_utils import (
    send_dataframe_to_sheets,
    transform_to_lists,
    get_dataframe_from_text_stream,
)


class TestPandasUtils(unittest.TestCase):
    @patch("src.stac_utils.pandas_utils.send_data_to_sheets")
    def test_send_dataframe_to_sheets(self, mock_google: MagicMock):
        """Test that the dataframe is sent to google sheets"""

        test_df = pd.DataFrame()
        send_dataframe_to_sheets(test_df, "foo", "bar")
        mock_google.assert_called_once_with([[]], "foo", "bar", "RAW", None)

    def test_transform_to_lists(self):
        """Test a dataframe is transformed into a list"""
        test_df = pd.DataFrame({"id": [1, 2, 3], "value": ["foo", "bar", "spam"]})
        test_list = transform_to_lists(test_df)

        self.assertListEqual(
            [["id", "value"], ["1", "foo"], ["2", "bar"], ["3", "spam"]], test_list
        )

    def test_transform_to_lists_with_none(self):
        """Test a dataframe is transformed into a list with None values"""
        test_df = pd.DataFrame({"id": [None], "value": [None]})
        test_list = transform_to_lists(test_df)

        self.assertListEqual([["id", "value"], ["", ""]], test_list)

    def test_transform_to_lists_empty_dataframe_with_columns(self):
        """Test an empty dataframe with columns is transformed into an empty list"""
        test_df = pd.DataFrame({"id": [], "value": []})
        test_list = transform_to_lists(test_df)

        self.assertListEqual([["id", "value"]], test_list)

    def test_transform_to_lists_empty_dataframe(self):
        """Test an empty dataframe is transformed into an empty list"""
        test_df = pd.DataFrame()
        test_list = transform_to_lists(test_df)

        self.assertListEqual([[]], test_list)

    @patch("builtins.open")
    @patch("src.stac_utils.pandas_utils.pd.read_csv")
    def test_get_dataframe_from_text_stream_with_header(
        self, mock_read_csv: MagicMock, mock_string_io: MagicMock
    ):
        mock_dataframe = MagicMock()
        mock_read_csv.return_value = mock_dataframe

        mock_data = StringIO("ColA,ColB\nfoo,bar\nspam,eggs")
        mock_string_io.getvalue.return_value = mock_data

        mock_columns = MagicMock()
        mock_dataframe.columns.return_value = mock_columns

        df = get_dataframe_from_text_stream(data=mock_data, delimiter=",", header=1)

        # assert no additional header columns created with header = 1
        self.assertEqual(df.columns.values.tolist(), [])

        # assert number of columns = 2 from test data
        self.assertEqual(len(mock_read_csv.call_args.kwargs["names"]), 2)

        # assert that final dataframe is same as reset_index() and tolist() operations on the read_csv output
        self.assertEqual(
            df.tolist(), mock_dataframe.__getitem__().reset_index().tolist()
        )

    @patch("builtins.open")
    @patch("src.stac_utils.pandas_utils.pd.read_csv")
    def test_get_dataframe_from_text_stream_without_header(
        self, mock_read_csv: MagicMock, mock_string_io: MagicMock
    ):
        mock_dataframe = MagicMock()
        mock_read_csv.return_value = mock_dataframe

        mock_data = StringIO("ColA,ColB,ColC\nfoo,bar,ham\nspam,eggs,baz")
        mock_string_io.getvalue.return_value = mock_data

        mock_columns = MagicMock()
        mock_dataframe.columns.return_value = mock_columns

        df = get_dataframe_from_text_stream(data=mock_data, delimiter=",", header=0)

        # assert two header columns created with header = 0
        self.assertEqual(df.columns, ["Col_0", "Col_1", "Col_2"])

        # assert number of columns = 3 from test data
        self.assertEqual(len(mock_read_csv.call_args.kwargs["names"]), 3)

        # assert that final dataframe is same as tolist() operation on the read_csv output
        self.assertEqual(df.tolist(), mock_dataframe.tolist())

    @patch("builtins.open")
    @patch("src.stac_utils.pandas_utils.pd.read_csv")
    def test_get_dataframe_from_text_stream_with_uneven_columns(
        self, mock_read_csv: MagicMock, mock_string_io: MagicMock
    ):
        mock_dataframe = MagicMock()
        mock_read_csv.return_value = mock_dataframe

        mock_data = StringIO("ColA,ColB\nfoo,bar\nspam,eggs,baz")
        mock_string_io.getvalue.return_value = mock_data

        mock_columns = MagicMock()
        mock_dataframe.columns.return_value = mock_columns

        df = get_dataframe_from_text_stream(data=mock_data, delimiter=",")

        # assert number of columns = 3 after creation of one column due to uneven data
        self.assertEqual(len(mock_read_csv.call_args.kwargs["names"]), 3)

        # assert that final dataframe is same as reset_index() and tolist() operations on the read_csv output
        self.assertEqual(
            df.tolist(), mock_dataframe.__getitem__().reset_index().tolist()
        )

    @patch("builtins.open")
    @patch("src.stac_utils.pandas_utils.pd.read_csv")
    def test_get_dataframe_from_text_stream_with_other_delimiter(
        self, mock_read_csv: MagicMock, mock_string_io: MagicMock
    ):
        mock_dataframe = MagicMock()
        mock_read_csv.return_value = mock_dataframe

        mock_data = StringIO("ColA,ColB,ColC|foo,bar,ham|spam,eggs,baz")
        mock_string_io.getvalue.return_value = mock_data

        mock_columns = MagicMock()
        mock_dataframe.columns.return_value = mock_columns

        df = get_dataframe_from_text_stream(data=mock_data, delimiter="|")

        # assert number of columns = 3
        self.assertEqual(len(mock_read_csv.call_args.kwargs["names"]), 3)

        # assert that final dataframe is same as reset_index() and tolist() operations on the read_csv output
        self.assertEqual(
            df.tolist(), mock_dataframe.__getitem__().reset_index().tolist()
        )


if __name__ == "__main__":
    unittest.main()
