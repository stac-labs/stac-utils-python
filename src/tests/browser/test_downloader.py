import unittest
from tempfile import TemporaryDirectory

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

    def test_check_for_new_files(self):
        """Test check for new files"""

    def test_check_for_new_files_all_finished(self):
        """Test check for new files when we've consumed all files"""
