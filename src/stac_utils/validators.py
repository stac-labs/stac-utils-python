import re

from email_validator import validate_email, EmailNotValidError


def email_validation(email) -> str:
    """
    Email validation method. Does not guess what the email is by removing not allowed characters;
    if email is not valid, it is removed.
    :param email: str, input email
    :return: email
    """
    # Set regex pattern
    html_pattern = re.compile("[\<\>]+|&#")

    # Handle NoneType
    email = email or ""

    # Html character exclusion and "/" character exclusion
    if html_pattern.search(email):
        email = ""
    elif "/" in email:
        email = ""

    # Using email validator package to validate email
    try:
        # Check that the email address is valid.
        validation = validate_email(email)
        # Return the normalized form of the email address
        email = validation.email
    except EmailNotValidError:
        email = ""
    finally:
        return email