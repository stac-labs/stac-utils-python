import os
import re
import unittest
from unittest.mock import MagicMock, patch, ANY

import requests

from src.stac_utils.email import Emailer, SMTPEmailer


class TestEmailer(unittest.TestCase):
    def test_init(self):
        """Test init method"""
        Emailer(
            "foo.bar",
            "spam",
            "spam@foo.bar",
            "spam@foo.bar",
        )

    def test_init_env_keys(self):
        """Test init method with env api keys"""
        test_keys = {"MAILGUN_API_KEY": "spam", "MAILGUN_DOMAIN": "foo.bar"}
        with patch.dict(os.environ, values=test_keys):
            test_emailer = Emailer()
            self.assertEqual("spam", test_emailer.api_key)
            self.assertEqual("foo.bar", test_emailer.domain)

    def test_init_no_keys(self):
        """Test init when no keys present anywhere"""
        self.assertRaises(KeyError, Emailer)

    @patch("requests.post")
    def test_send_email(self, mock_post: MagicMock):
        """Test send email"""
        test_emailer = Emailer("foo", "bar")
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        test_emailer.send_email("foo", body="bar", emails=["spam@foo.bar"])
        mock_post.assert_called_once_with(
            "https://api.mailgun.net/v3/foo/messages",
            auth=("api", "bar"),
            data={
                "to": "spam@foo.bar",
                "from": None,
                "subject": "foo",
                "h:Reply-to": [],
                "html": "bar",
            },
        )
        mock_response.raise_for_status.assert_called_once()

    def test_send_email_no_body_no_template(self):
        """Test send email with no body and no template"""

        test_emailer = Emailer("foo", "bar")
        self.assertRaises(
            ValueError, test_emailer.send_email, "foo", emails=["spam@foo.bar"]
        )

    @patch("requests.post")
    def test_send_email_with_template(self, mock_post: MagicMock):
        """Test send email"""
        test_emailer = Emailer("foo", "bar")
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        test_emailer.send_email(
            "foo",
            template="barTemplate",
            variables={"variable": "misc"},
            emails=["spam@foo.bar"],
        )
        mock_post.assert_called_once_with(
            "https://api.mailgun.net/v3/foo/messages",
            auth=("api", "bar"),
            data={
                "to": "spam@foo.bar",
                "from": None,
                "subject": "foo",
                "h:Reply-to": [],
                "template": "barTemplate",
                "t:variables": '{"variable": "misc"}',
            },
        )
        mock_response.raise_for_status.assert_called_once()

    @patch("requests.post")
    def test_send_email_custom_reply_to(self, mock_post: MagicMock):
        """Test send email with custom reply to"""
        test_emailer = Emailer("foo", "bar", reply_to="no@foo.bar")
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        test_emailer.send_email(
            "foo", body="bar", emails=["spam@foo.bar"], reply_to="yes@foo.bar"
        )
        mock_post.assert_called_once_with(
            "https://api.mailgun.net/v3/foo/messages",
            auth=("api", "bar"),
            data={
                "to": "spam@foo.bar",
                "from": None,
                "subject": "foo",
                "h:Reply-to": ["yes@foo.bar"],
                "html": "bar",
            },
        )
        mock_response.raise_for_status.assert_called_once()

    @patch("requests.post")
    def test_send_email_custom_from(self, mock_post: MagicMock):
        """Test send email with custom from"""

        test_emailer = Emailer("foo", "bar", from_addr="no@foo.bar")
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        test_emailer.send_email(
            "foo", body="bar", emails=["spam@foo.bar"], from_addr="yes@foo.bar"
        )
        mock_post.assert_called_once_with(
            "https://api.mailgun.net/v3/foo/messages",
            auth=("api", "bar"),
            data={
                "to": "spam@foo.bar",
                "from": "yes@foo.bar",
                "subject": "foo",
                "h:Reply-to": [],
                "html": "bar",
            },
        )
        mock_response.raise_for_status.assert_called_once()

    @patch("requests.post")
    def test_send_email_error(self, mock_post: MagicMock):
        """Test send email with error"""

        test_emailer = Emailer("foo", "bar")
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock(
            side_effect=requests.exceptions.RequestException
        )
        mock_post.return_value = mock_response
        self.assertRaises(
            requests.exceptions.RequestException,
            test_emailer.send_email,
            "foo",
            body="bar",
            emails=["spam@foo.bar"],
        )


class TestSMTPEmailer(unittest.TestCase):
    @patch("src.stac_utils.email.SMTP_SSL")
    def test_init(self, mock_smtp: MagicMock):
        """Test init method"""
        test_emailer = SMTPEmailer("foo@bar", "spam")
        mock_smtp.assert_called_once()
        test_emailer.client.ehlo.assert_called_once()
        test_emailer.client.login.assert_called_once_with("foo@bar", "spam")

    @patch("src.stac_utils.email.SMTP_SSL")
    def test_init_env_keys(self, mock_smtp: MagicMock):
        """Test init method with env api keys"""
        test_keys = {"GOOGLE_USERNAME": "foo@bar", "GOOGLE_APP_PASSWORD": "spam"}
        with patch.dict(os.environ, values=test_keys):
            test_emailer = SMTPEmailer()
            self.assertEqual("spam", test_emailer.password)
            self.assertEqual("foo@bar", test_emailer.username)
            mock_smtp.assert_called_once()
            test_emailer.client.ehlo.assert_called_once()
            test_emailer.client.login.assert_called_once_with("foo@bar", "spam")

    def test_init_no_keys(self):
        """Test init when no keys present anywhere"""
        self.assertRaises(KeyError, SMTPEmailer)

    @patch("src.stac_utils.email.SMTP_SSL")
    def test_send_email(self, mock_smtp: MagicMock):
        """Test send email"""
        test_emailer = SMTPEmailer("foo@bar", "spam")
        test_emailer.send_email("foo", body="foobarspam", emails=["spam@foo.bar"])
        test_emailer.client.sendmail.assert_called_once_with(
            "foo@bar", ["spam@foo.bar"], ANY
        )
        argument_string = test_emailer.client.sendmail.call_args[0][2]
        assert re.search("To: spam@foo.bar", argument_string)
        assert re.search("From: foo@bar", argument_string)
        assert re.search("Subject: foo", argument_string)
        assert re.search("foobarspam", argument_string)

    @patch("src.stac_utils.email.SMTP_SSL")
    def test_send_email_no_body(self, mock_smtp: MagicMock):
        """Test send email with no body"""

        test_emailer = SMTPEmailer("foo@bar", "spam")
        self.assertRaises(
            TypeError, test_emailer.send_email, "foo", emails=["spam@foo.bar"]
        )

    @patch("src.stac_utils.email.SMTP_SSL")
    def test_send_email_custom_reply_to(self, mock_stmp: MagicMock):
        """Test send email with custom reply to"""
        test_emailer = SMTPEmailer("foo@bar", "spam")
        test_emailer.send_email(
            "foo",
            body="foobarspam",
            emails=["spam@foo.bar", "spamB@foo.bar"],
            reply_to=["spamC@foo.bar", "spamD@foo.bar"],
        )
        test_emailer.client.sendmail.assert_called_once_with(
            "foo@bar", ["spam@foo.bar", "spamB@foo.bar"], ANY
        )
        argument_string = test_emailer.client.sendmail.call_args[0][2]
        assert re.search("To: spam@foo.bar,spamB@foo.bar", argument_string)
        assert re.search("Reply-To: spamC@foo.bar,spamD@foo.bar", argument_string)


if __name__ == "__main__":
    unittest.main()
