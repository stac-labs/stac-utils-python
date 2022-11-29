import unittest

from src.stac_utils.pandas_utils import send_data_to_sheets, transform_to_lists


class TestPandasUtils(unittest.TestCase):
    def test_send_dataframe_to_sheets(self):
        """ Test that the dataframe is sent to google sheets """

    def test_transform_to_lists(self):
        """ Test a dataframe is transformed into a list """

    def test_transform_to_lists_empty_dataframe(self):
        """ Test an empty dataframe is transformed into an empty list """


if __name__ == '__main__':
    unittest.main()
