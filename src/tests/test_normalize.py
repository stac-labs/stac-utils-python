import unittest

from src.stac_utils.normalize import normalize_email, normalize_zip


class TestNormalize(unittest.TestCase):
    """Testing that various inputs yield expected results for normalizing emails, zips, proper names"""

    def test_normalize_email(self):
        emails_to_test = [
            # standard types of email strings
            ("foo@bar.com", "foo@bar.com"),
            ("Foo1@bar.com", "Foo1@bar.com"),
            ("12345@foo.com", "12345@foo.com"),
            # html character and "/" character exclusion
            ("<foo>@bar.com", ""),
            ("foo/bar@spam.com", ""),
            # NoneType
            (None, ""),
            ("", ""),
        ]

        for test_email, expected_email in emails_to_test:
            self.assertEqual(expected_email, normalize_email(test_email))

    def test_normalize_zip(self):
        zips_to_test = [
            # standard zip 5
            ("12345", "12345"),
            # non-numeric characters
            ("abcde", ""),
            ("123/5", ""),
            ("#1234", ""),
            # inputs with lengths != 5
            ("1234", ""),
            ("123456", "12345"),
            # NoneType
            (None, ""),
            ("", ""),
        ]

        for test_zip, expected_zip in zips_to_test:
            self.assertEqual(expected_zip, normalize_zip(test_zip))

    if __name__ == "__main__":
        unittest.main()
