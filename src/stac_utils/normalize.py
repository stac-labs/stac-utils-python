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


def name_and_place_validation(name_or_place_input) -> str:
    """
    General validation for input fields, removing numbers, html tags and html special characters
    :param name_or_place_input: str, the input field (i.e. city, first_name, last_name)
    :return: str, the name or place input is returned after validation
    """
    # Set regex pattern
    html_pattern = re.compile("[\<\>]+|&#|[0-9]")

    # Handle NoneType
    name_or_place_input = name_or_place_input or ""

    # Remove html patterns and capitalize first letter of every word
    name_or_place_input = html_pattern.sub("", name_or_place_input).title()

    return name_or_place_input


def zip_validation(zip_input) -> str:
    """
    Formats input zip to zip code 5
    :param zip_input: str, zipcode value from Actionkit
    :return: str, zip_input
    """
    # Set regex pattern
    html_pattern = re.compile("[^0-9]")

    # Handle NoneType
    zip_input = zip_input or ""

    # Remove anything that is not a number
    zip_input = html_pattern.sub("", zip_input)

    # limit to zip5
    zip_input = zip_input[:5]
    if len(zip_input) != 5:
        zip_input = ""

    return zip_input
