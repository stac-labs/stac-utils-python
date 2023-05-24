import unittest
from unittest.mock import MagicMock, patch, call


from src.stac_utils.browser.downloader import Downloader


class TestDownloader(unittest.TestCase):
    def setUp(self):
        """Setup temporary directory with temp files to examine"""

    def test_init(self):
        """Test init"""

        test_downloader = Downloader(".")
        self.assertEqual(test_downloader.directory, ".")

    def test_clear(self):
        """Test clear"""

        test_downloader = Downloader(".")
        test_downloader.returned_files.add("Foo")
        test_downloader.clear()
        self.assertEqual(len(test_downloader.returned_files), 0)

    def test_check_for_new_files(self):
        """Test check for new files"""

    def test_check_for_new_files_with_provided_pattern(self):
        """Test check for new files when alternate pattern is provided"""

    def test_check_for_new_files_all_finished(self):
        """Test check for new files when we've consumed all files"""

    def test_check_for_new_files_still_downloading(self):
        """Test check for new files when a file is still downloading"""
