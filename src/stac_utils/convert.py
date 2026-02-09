import re

from typing import Any, Optional

def _convert(camel_input: str) -> str:
    # from https://stackoverflow.com/a/46493824

    words = re.findall(r"[A-Z]?[a-z]+|[A-Z]{2,}(?=[A-Z][a-z]|\d|\W|$)|\d+", camel_input)
    return "_".join(map(str.lower, words))


def convert_to_snake_case(data: [str, dict, list]) -> [str, dict, list]:
    """
    Converts provided data to snake case

    :param data: Data to convert to snake case
    :return: Data reformatted as snake case
    """
    if type(data) is list:
        return [convert_to_snake_case(row) for row in data]
    elif type(data) is str:
        return _convert(data)

    new_data = {}
    for k, v in data.items():
        k = _convert(k)
        if isinstance(v, list):
            v = [convert_to_snake_case(row) for row in v]
        new_data[k] = v

    return new_data


def strip_dict(full_dict: dict):
    """Removes None values from dictionaries
    :param full_dict: dict to clean up
    :return: dict without None values"""
    return {k: v for k, v in full_dict.items() if v is not None}

def get_first_value(row: dict, keys: list[str]) -> tuple[Optional[Any], Optional[str]]:
    """
    Get the first non-None/non-empty value from a list of possible keys.
    
    Returns:
        tuple: (value, key_used) or (None, None) if no value found.
    """
    for key in keys:
        value = row.get(key)
        if value is not None and value != "":
            return value, key
    return None, None


def get_all_values(row: dict, keys: list[str]) -> dict[str, Any]:
    """
    Get all non-None/non-empty values from a list of possible keys.
    
    Returns:
        dict: {key: value} for all keys that have values.
    """
    return {
        key: row.get(key) 
        for key in keys 
        if row.get(key) is not None and row.get(key) != ""
    }
