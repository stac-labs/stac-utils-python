import unittest
from unittest.mock import MagicMock, patch, call

from src.stac_utils.browser.driver import ChromeDriver


class TestChromeDriver(unittest.TestCase):
    def test_init(self):
        """Test init"""

    def test_init_temp_dir(self):
        """Test init with temp dir"""

    def test_init_headless(self):
        """Test init as headless"""

    def test_init_env_locations(self):
        """Test init with env location specified"""

    def test_init_no_locations(self):
        """Test init with no locations specified"""

    def test_init_not_local_no_binary(self):
        """Test init not locally and no binary location"""

    def test_init_not_local_no_driver(self):
        """Test init not locally and no driver location"""

    def test_init_local_no_driver(self):
        """Test init run locally and no driver location"""

    def test_context_manager(self):
        """Test context manager"""

    def test_context_manager_temp_dir(self):
        """Test context manager with temp dir"""
