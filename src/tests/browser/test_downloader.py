import unittest
from unittest.mock import MagicMock, patch, call


from src.stac_utils.browser.downloader import Downloader


mock_sleep = MagicMock()
mock_getsize = MagicMock()
mock_glob = MagicMock()


@patch("time.sleep", new=mock_sleep)
@patch("os.path.getsize", new=mock_getsize)
@patch("glob.glob", new=mock_glob)
class TestDownloader(unittest.TestCase):
    def setUp(self):
        """Setup temporary directory with temp files to examine"""

        self.test_downloader = Downloader(".", polling=42.0, pattern="foo*.csv")

    def test_init(self):
        """Test init"""

        self.assertEqual(self.test_downloader.directory, ".")
        self.assertEqual(self.test_downloader.polling, 42.0)
        self.assertEqual(self.test_downloader.pattern, "foo*.csv")

    def test_clear(self):
        """Test clear"""

        self.test_downloader.returned_files.add("Foo")
        self.test_downloader.clear()
        self.assertEqual(len(self.test_downloader.returned_files), 0)

    def test_check_for_new_files(self):
        """Test check for new files"""

        # first have no files, then have a file on second call
        mock_glob.side_effect = [[]] + [["foo.csv"]] * 4
        mock_getsize.side_effect = [2, 2]

        test_files = list(self.test_downloader.check_for_new_files())
        self.assertEqual(test_files, ["foo.csv"])
        mock_glob.assert_called_with("./foo*.csv")
        # now test that it exits because all files have been collected
        test_files = list(self.test_downloader.check_for_new_files())
        self.assertEqual(test_files, [])

    def test_check_for_new_files_with_provided_pattern(self):
        """Test check for new files when alternate pattern is provided"""

        # first have no files, then have a file on second call
        mock_glob.side_effect = [[]] + [["bar.csv"]] * 3
        mock_getsize.side_effect = [2, 2]

        test_files = list(self.test_downloader.check_for_new_files("bar*.csv"))
        self.assertEqual(test_files, ["bar.csv"])
        mock_glob.assert_called_with("./bar*.csv")

    def test_check_for_new_files_still_downloading(self):
        """Test check for new files when a file is still downloading"""

        # first have no files, then have a file on second call
        mock_glob.side_effect = [[]] + [["foo.csv"]] * 4

        mock_getsize.side_effect = [1, 2, 2]

        test_files = list(self.test_downloader.check_for_new_files())
        self.assertEqual(test_files, ["foo.csv"])
