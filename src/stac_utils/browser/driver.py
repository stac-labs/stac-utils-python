import os
import tempfile

from selenium.webdriver import ChromeOptions
from undetected_chromedriver._compat import Chrome
from webdriver_manager.chrome import ChromeDriverManager


class ChromeDriver:
    """ Chrome drive sugar that loads in some intelligent defaults for setting up
        a headless version for scripts.

        By default, it'll use a temporary directory for downloaded files.
    """
    def __init__(self, download_directory: str = None, is_headless: bool = True):
        self.temp_dir = None
        self.download_directory = download_directory
        self.is_headless = is_headless
        self.driver = None

    def __enter__(self):
        if self.download_directory is None:
            self.temp_dir = tempfile.TemporaryDirectory()
            self.download_directory = self.temp_dir.name

        options = ChromeOptions()
        options.add_experimental_option(
            "prefs", {"download.default_directory": self.download_directory}
        )
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280x1696")
        options.add_argument("--single-process")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-dev-tools")
        options.add_argument("--no-zygote")

        if os.environ.get("CHROME_BINARY"):
            options.binary_location = os.environ.get("CHROME_BINARY")
        if self.is_headless:
            options.add_argument("--headless")

        path = ChromeDriverManager().install()

        self.driver = Chrome(options=options, executable_path=path)

        """ Tack the (temp) download directory onto the driver object
            so it can be referenced by the script
        """

        self.driver.download_directory = self.download_directory

        return self.driver

    def __exit__(self, *args):
        if self.driver:
            self.driver.close()

        if self.temp_dir:
            self.temp_dir.cleanup()
