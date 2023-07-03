import hashlib
import hmac
import os
import time

import requests
import xmltodict

from .http import HTTPClient


class BSDClient(HTTPClient):
    """"""

    api_ver = 2  # BSD API ID - always 2

    def __init__(
        self,
        bsd_url: str = None,
        bsd_api_id: str = None,
        bsd_api_secret: str = None,
        *args,
        **kwargs,
    ):
        self.base_url = bsd_url or os.environ["BSD_URL"]
        self.bsd_api_id = bsd_api_id or os.environ["BSD_API_ID"]
        self.bsd_api_secret = bsd_api_secret or os.environ["BSD_API_SECRET"]

        super().__init__(*args, **kwargs)

    def generate_api_mac(self, current_time: str, url: str, params: dict = None):
        params_str = f"api_ver=2&api_id={self.bsd_api_id}&api_ts={current_time}"

        if params:
            for k, v in params.items():
                params_str += f"&{k}={v}"

        signing_str = (
            self.bsd_api_id
            + os.linesep
            + current_time
            + os.linesep
            + url
            + os.linesep
            + params_str
        )

        api_mac = hmac.new(
            self.bsd_api_secret.encode(), signing_str.encode(), hashlib.sha1
        ).hexdigest()

        return api_mac

    def call_api(
        self,
        method: str,
        endpoint: str,
        params: dict = None,
        body: dict = None,
        return_headers: bool = False,
        use_snake_case: bool = True,
        override_error_logging: bool = False,
        override_data_printing: bool = False,
        **kwargs,
    ):
        current_time = str(int(time.time()))
        api_mac = self.generate_api_mac(current_time, endpoint, params)

        new_params = {
            "api_ver": self.api_ver,
            "api_id": self.bsd_api_id,
            "api_ts": current_time,
            "api_mac": api_mac,
        }

        new_params.update(**params)
        super().call_api(
            method,
            endpoint,
            params=new_params,
            body=body,
            return_headers=return_headers,
            use_snake_case=use_snake_case,
            override_error_logging=override_error_logging,
            override_data_printing=override_data_printing,
            **kwargs,
        )

    def transform_response(self, response: requests.Response, **kwargs):
        return xmltodict.parse(response.text, xml_attribs=False)
