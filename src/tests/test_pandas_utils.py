import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from src.stac_utils.pandas_utils import send_dataframe_to_sheets, transform_to_lists


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


if __name__ == "__main__":
    unittest.main()
