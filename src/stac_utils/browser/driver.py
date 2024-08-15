import os
import tempfile

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class ChromeDriver:
    """Chrome drive sugar that loads in some intelligent defaults for setting up
    a headless version for scripts.

    By default, it'll use a temporary directory for downloaded files.
    """

    def __init__(
        self,
        download_directory: str = None,
        is_headless: bool = True,
        run_locally: bool = False,
        binary_location: str = None,
        driver_location: str = None,
    ):
        self.temp_dir = None
        self.download_directory = download_directory
        self.binary_location = binary_location or os.environ.get("CHROME_BINARY")
        self.driver_location = driver_location or os.environ.get("CHROME_DRIVER")
        self.run_locally = run_locally

        # if it's not being run locally then it must be headless
        self.is_headless = is_headless or not self.run_locally

        if not self.run_locally and not self.binary_location:
            self.binary_location = "/opt/chrome/chrome"
        if not self.run_locally and not self.driver_location:
            self.driver_location = "/opt/chromedriver"
        elif not self.driver_location:
            self.driver_location = ChromeDriverManager().install()
        self.driver = None

    def __enter__(self):
        service = Service(
            self.driver_location,
            service_args=["--enable-logging=stdout"],
            log_path="/tmp/chromedriver.log",
            # log_path=None if self.run_locally else "/tmp/chromedriver.log",
        )
        if self.download_directory is None:
            self.temp_dir = tempfile.TemporaryDirectory()
            self.download_directory = self.temp_dir.name

        options = webdriver.ChromeOptions()
        if self.binary_location:
            options.binary_location = self.binary_location
        if not self.run_locally:
            options.add_argument("--single-process")
        if self.is_headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280x1696")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-dev-tools")
        options.add_argument("--disable-blink-features=AutomationControlled") 
        options.add_argument("--no-zygote")
        options.add_argument("--disable-dev-tools")
        options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")
        options.add_argument(f"--data-path={tempfile.mkdtemp()}")
        options.add_argument(f"--disk-cache-dir={tempfile.mkdtemp()}")
        options.add_experimental_option(
            "prefs", {"download.default_directory": self.download_directory}
        )
        options.add_experimental_option("useAutomationExtension", False) 

        self.driver = webdriver.Chrome(service=service, options=options)

        """ Tack the (temp) download directory onto the driver object
            so it can be referenced by the script
        """
        self.driver.download_directory = self.download_directory

        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 

        print('working off the browser tricks repo')

        return self.driver

    def __exit__(self, *args):
        if self.driver:
            self.driver.close()
            self.driver = None

        if self.temp_dir:
            self.temp_dir.cleanup()
            self.temp_dir = None
