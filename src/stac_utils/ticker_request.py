import logging
import os
import requests

from typing import List

from .http import HTTPClient

logger = logging.getLogger(__name__)

'''
Sample code:
from stac_utils.ticker_request import TickerRequest
from stac_utils import secrets # only necessary in AWS

with secrets(secret_name = 'TICKER_SECRET_NAME'): # with secrets() only in AWS
    ticker = TickerRequest()
    ticker.add_data('FL', 'AWS Lambda', 'event-sync', 'events created', 155)
    ticker.add_data('FL', 'AWS Lambda', 'event-sync', 'signups created', 1342)

    result = ticker.send_to_ticker()
    if result.status_code != 200:
        raise Exception('Metrics not sent to ticker')
'''

class TickerRequest(HTTPClient):
    if (
        os.environ['TICKER_URL']
        and os.environ['AUTH_USER']
        and os.environ['AUTH_PASS']
    ):
        base_url = os.environ['TICKER_URL']
    else:
        error = 'Ticker authentication or URL missing from environment'
        logger.error(error)
        raise Exception(error)

    def __init__(self, *args, **kwargs):
        self.data: List[dict] = []
        super().__init__(*args, **kwargs)
    
    def create_session(self) -> requests.Session:
        session = requests.Session()
        session.auth = (os.environ['AUTH_USER'], os.environ['AUTH_PASS'])

        return session
    
    def transform_response(
        self,
        response: requests.Response,
        return_headers: bool = False,
        use_snake_case: bool = False
    ):
        return response
    
    def check_for_error(
        self,
        response: requests.Response,
        data: dict,
        override_error_logging: bool = False
    ):
        if response.status_code != 200:
            logger.error(response.content)
            raise Exception(response.content)

    def add_data(
        self,
        state: str,
        source: str,
        task: str,
        metric: str,
        amount: float
    ):
        self.data.append({
            'state': state,
            'source': source,
            'task': task,
            'metric': metric,
            'amount': amount
        })

    def send_to_ticker(self):
        return self.post('/ticker', body = self.data)