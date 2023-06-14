import json
import os
import requests

from . import listify


class Emailer:
    """
    Sets up Mailgun Emailer
    """

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
        body: str = None,
        emails: list[str] = None,
        from_addr: str = None,
        reply_to: str = None,
        template: str = None,
        variables: dict = None,
    ):
        """
        Sends email given specified details. Either include the body with the raw HTML directly, or template and variables so the template will be utilized.

        :param subject: Desired subject for email
        :param body: Body of email
        :param emails: List of email addresses receiving email
        :param from_addr: From address for email
        :param reply_to: Reply-to for email
        :param template: Specified template for email
        :param variables: Specified variables for email template
        """
        email_data = {
            "to": ",".join(emails),
            "from": from_addr or self.from_addr,
            "subject": subject,
            "h:Reply-to": listify(reply_to) or self.reply_to,
        }

        if body:
            email_data["html"] = body
        elif template and variables:
            email_data["template"] = template
            email_data["t:variables"] = json.dumps(variables)
        else:
            raise ValueError("body or template must be provided")

        request_url = f"https://api.mailgun.net/v3/{self.domain}/messages"

        resp = requests.post(request_url, auth=("api", self.api_key), data=email_data)
        resp.raise_for_status()
