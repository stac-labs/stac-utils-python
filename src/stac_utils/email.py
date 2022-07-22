import os
from typing import List
import requests

from . import listify

class Emailer:
    def __init__(
        self,
        domain: str = None,
        api_key: str = None,
        from_addr: str = None,
        reply_to: str = None,
    ):
        self.api_key = api_key or os.environ["MAILGUN_API_KEY"]
        self.domain = domain or os.environ["MAILGUN_DOMAIN"]
        self.from_addr = from_addr
        self.reply_to = listify(reply_to)

    def send_email(
        self,
        subject: str,
        body: str,
        emails: List[str],
        from_addr: str = None,
        reply_to: str = None,
    ):
        email_data = {
            "to": ",".join(emails),
            "from": from_addr or self.from_addr,
            "subject": subject,
            "text": "",
            "html": body,
            "h:Reply-to": listify(reply_to) or self.reply_to,
        }

        request_url = f"https://api.mailgun.net/v3/{self.domain}/messages"

        resp = requests.post(request_url, auth=("api", self.api_key), data=email_data)
        resp.raise_for_status()
