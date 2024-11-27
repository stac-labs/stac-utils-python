import json
import os
import requests

from smtplib import SMTP_SSL
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
        cleaned_emails = [email.strip() for email in emails]
        email_data = {
            "to": ",".join(cleaned_emails),
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


class SMTPEmailer:
    """
    Sets up SMTP Emailer for Google accounts, if an app password is enabled.
    """

    def __init__(
        self,
        username: str = None,
        password: str = None,
    ):
        self.username = username or os.environ["GOOGLE_USERNAME"]
        self.password = password or os.environ["GOOGLE_APP_PASSWORD"]
        self.client = SMTP_SSL("smtp.gmail.com", 465)
        self.client.ehlo()
        self.client.login(self.username, self.password)

    def send_email(
        self,
        subject: str,
        body: str,
        emails: list[str] = None,
        reply_to: list[str] = None,
    ):
        """
        Sends email given specified details. Include the body with the raw HTML directly.

        :param subject: Subject of email
        :param body: Body of email
        :param emails: List of email addresses receiving email
        :param reply_to: List of reply-to addresses for email
        """
        email_data = MIMEMultipart()
        email_data["To"] = ",".join(emails)
        email_data["From"] = self.username
        email_data["Subject"] = subject
        if reply_to:
            email_data["Reply-To"] = ",".join(reply_to)
        email_data.attach(MIMEText(body, "html"))

        return self.client.sendmail(self.username, emails, email_data.as_string())
