import os
import unittest
from unittest.mock import MagicMock, patch

import requests

from src.stac_utils.email import Emailer


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
            self.assertEqual(test_emailer.api_key, "spam")
            self.assertEqual(test_emailer.domain, "foo.bar")

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
            f"https://api.mailgun.net/v3/foo/messages",
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
            f"https://api.mailgun.net/v3/foo/messages",
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
            f"https://api.mailgun.net/v3/foo/messages",
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


if __name__ == "__main__":
    unittest.main()
