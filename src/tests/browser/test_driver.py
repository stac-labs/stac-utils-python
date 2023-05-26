import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch, call

from src.stac_utils.browser.driver import ChromeDriver


mock_manager = MagicMock()
mock_service = MagicMock()
mock_webdriver = MagicMock()


@patch("src.stac_utils.browser.driver.webdriver", new=mock_webdriver)
@patch("src.stac_utils.browser.driver.Service", new=mock_service)
@patch("src.stac_utils.browser.driver.ChromeDriverManager", new=mock_manager)
class TestChromeDriver(unittest.TestCase):
    def test_init(self):
        """Test init"""

        test_driver = ChromeDriver()
        # check defaults
        self.assertEqual(test_driver.binary_location, "/opt/chrome/chrome")
        self.assertEqual(test_driver.driver_location,  "/opt/chromedriver")
        self.assertFalse(test_driver.run_locally)
        self.assertTrue(test_driver.is_headless)
        self.assertIsNone(test_driver.download_directory)

    def test_init_download_dir(self):
        """Test init with download dir"""

        test_driver = ChromeDriver(download_directory="./foo")
        self.assertEqual(test_driver.download_directory, "./foo")

    def test_init_headless(self):
        """Test init as headless"""

        test_driver = ChromeDriver(is_headless=True)
        self.assertTrue(test_driver.is_headless)

    def test_init_env_locations(self):
        """Test init with env location specified"""

        mock_environ = {
            "CHROME_BINARY": "./foo",
            "CHROME_DRIVER": "./bar",
        }

        with patch.dict(os.environ, values=mock_environ):
            test_driver = ChromeDriver()
            self.assertEqual(test_driver.binary_location, "./foo")
            self.assertEqual(test_driver.driver_location,  "./bar")

    def test_init_local_no_driver(self):
        """Test init run locally and no driver location"""

        test_driver = ChromeDriver(run_locally=True)
        mock_manager.install.assert_called_once()

    @patch("tempfile.TemporaryDirectory")
    def test_context_manager(self, mock_temp_dir: MagicMock):
        """Test context manager"""

        mock_temp_dir.name.return_value = "./foo"

        with ChromeDriver() as test_driver:
            mock_temp_dir.assert_called_once_with()
            mock_webdriver.ChromeOptions.assert_called_once_with()
            mock_webdriver.Chrome.assert_called_once()
            self.assertEqual(test_driver.download_directory, "./foo")

        mock_webdriver.Chrome.close.assert_called_once()

    @patch("tempfile.TemporaryDirectory")
    def test_context_manager_with_download_dir(self, mock_temp_dir: MagicMock):
        """Test context manager with download dir"""

        with ChromeDriver(download_directory="./foo") as test_driver:
            mock_temp_dir.assert_not_called()
            self.assertEqual(test_driver.download_directory, "./foo")

        mock_temp_dir.cleanup.assert_called_once()
