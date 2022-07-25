import re
from typing import Union


def _convert(camel_input: str) -> str:
    # from https://stackoverflow.com/a/46493824

    words = re.findall(r"[A-Z]?[a-z]+|[A-Z]{2,}(?=[A-Z][a-z]|\d|\W|$)|\d+", camel_input)
    return "_".join(map(str.lower, words))


def convert_to_snake_case(data: Union[dict, list]) -> Union[dict, list]:
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
