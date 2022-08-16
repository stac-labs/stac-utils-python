TRUE_VALUES = ["1", "T", "TRUE", "Y", "YES"]


def truthy(thing: str, true_values: list = None) -> bool:
    true_values = true_values if true_values is not None else TRUE_VALUES
    return str(thing).upper() in true_values
