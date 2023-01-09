import unittest

from src.stac_utils.email import Emailer


class TestEmailer(unittest.TestCase):
    def test_init(self):
        """Test init method"""
        Emailer(
            "mail.staclabs.io",
            "API_KEY",
            "engineering@staclabs.io",
            "engineering@staclabs.io",
        )

    def test_init_no_keys(self):
        """Test init uses keys from environment"""
        self.assertRaises(KeyError, lambda: Emailer())

    def test_send_email(self):
        """Test send email"""

    def test_send_email_custom_reply_to(self):
        """Test send email with custom reply to"""

    def test_send_email_custom_from(self):
        """Test send email with custom from"""

    def test_send_email_error(self):
        """Test send email with error"""


if __name__ == "__main__":
    unittest.main()
