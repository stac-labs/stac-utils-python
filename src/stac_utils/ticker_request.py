import logging
import os
import requests

from .http import HTTPClient

logger = logging.getLogger(__name__)


class TickerException(Exception):
    pass


class TickerAuthException(TickerException):
    pass


class TickerRequest(HTTPClient):
    """
    Usage:
    from stac_utils.ticker_request import TickerRequest
    from stac_utils import secrets # only necessary in AWS

    # with secrets() context only needed in AWS
    with secrets(secret_name = os.environ['TICKER_SECRET_NAME']):
        ticker = TickerRequest()
        ticker.add_data('FL', 'AWS Lambda', 'event-sync', 'events created', 155)
        ticker.add_data('FL', 'AWS Lambda', 'event-sync', 'signups created', 1342)

        ticker.send_to_ticker()
    """

    def __init__(self, *args, **kwargs):
        if (
            os.environ.get("TICKER_URL")
            and os.environ.get("AUTH_USER")
            and os.environ.get("AUTH_PASS")
        ):
            self.base_url = os.environ["TICKER_URL"]
        else:
            error = "Ticker authentication or URL missing from environment"
            logger.error(error)
            raise TickerAuthException(error)

        self.data: list[dict] = []
        super().__init__(*args, **kwargs)

    def create_session(self) -> requests.Session:
        """
        Creates session for ticker
        """
        session = requests.Session()
        session.auth = (os.environ["AUTH_USER"], os.environ["AUTH_PASS"])

        return session

    def transform_response(
        self,
        response: requests.Response,
        return_headers: bool = False,
        use_snake_case: bool = False,
    ):
        """
        Transforms and returns response given specifications

        :param response: API response
        :param return_headers: `False` by default, set `True` if return headers desired
        :param use_snake_case: `False` by default, set `True` if snake case desired
        :return: Transformed response
        """
        return response

    def check_for_error(
        self,
        response: requests.Response,
        data: dict,
        override_error_logging: bool = False,
    ):
        """
        Checks response for errors, logs response content, and raises TickerException if errors exist

        :param response: API response
        :param data: Data
        :param override_error_logging: `False` by default, set `True` if overriding logging errors desired
        :raises: TickerException if response status code is not 200
        """
        if response.status_code != 200:
            logger.error(response.content)
            raise TickerException(response.content)

    def add_data(self, state: str, source: str, task: str, metric: str, amount: float):
        """
        Appends ticker data given specified information

        :param state: Relevant state
        :param source: Data source
        :param task: Ticker task
        :param metric: Ticker metric for task
        :param amount: Amount of metric to append to ticker data
        """
        self.data.append(
            {
                "state": state,
                "source": source,
                "task": task,
                "metric": metric,
                "amount": amount,
                "is_testing": os.environ.get("IS_TESTING", ""),
            }
        )

    def send_to_ticker(self):
        """
        Sends data to ticker if it exists, raises TickerException if error
        """
        if len(self.data) > 0:
            result = self.post("/ticker", body=self.data)

            if result.status_code == 200:
                self.data = []
                return result
            else:
                logger.error(result)
                raise TickerException("Metrics not sent to ticker")
        else:
            logger.info("No data to send to ticker")
            return
