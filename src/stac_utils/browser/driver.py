import os
import tempfile

from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager


class ChromeDriver:
    """Chrome drive sugar that loads in some intelligent defaults for setting up
    a headless version for scripts.

    By default, it'll use a temporary directory for downloaded files.
    """

    def __init__(
        self,
        chrome_binary: str = None,
        chrome_driver: str = None,
        download_directory: str = None,
        is_headless: bool = True,
    ):
        self.chrome_binary = chrome_binary or os.environ.get("CHROME_BINARY")
        self.chrome_driver = chrome_driver or os.environ.get("CHROME_DRIVER")
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
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280x1696")
        options.add_argument("--single-process")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-dev-tools")
        options.add_argument("--no-zygote")

        if self.chrome_binary:
            print(f"binary location: {self.chrome_binary}")
            options.binary_location = self.chrome_binary
        if self.is_headless:
            options.add_argument("--headless")

        # automatically retrieve a chrome driver if one isn't specified
        driver_path = self.chrome_driver or ChromeDriverManager().install()
        print(f"driver location: {driver_path}")
        self.driver = webdriver.Chrome(
            options=options,
            service=ChromeService(
                executable_path=driver_path,
                service_args=["--enable-logging=stdout"],
            ),
        )

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
