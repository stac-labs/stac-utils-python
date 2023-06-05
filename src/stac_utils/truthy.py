TRUE_VALUES = ["1", "T", "TRUE", "Y", "YES"]


def truthy(thing: str, true_values: list = None) -> bool:
    """
    Evaluates whether a string is `True`

    :param thing: Item to evaluate
    :param true_values: Optional list of alternate `True` values
    :return: `True` if a truthy value, `False` if anything else
    """
    true_values = true_values if true_values is not None else TRUE_VALUES
    return str(thing).upper() in true_values
