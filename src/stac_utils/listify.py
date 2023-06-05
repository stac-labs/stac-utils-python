def listify(
    string: str,
    type_: type = str,
    sep: str = ",",
    ignore_errors: bool = False,
    ignore_empty: bool = True,
) -> list:
    """
    Split a string into a list, converting to a type as necessary

    :param string:
    :param type_:
    :param sep:
    :param ignore_errors:
    :param ignore_empty:
    :return:
    :raises:
    """
    if string is None:
        return []

    if not string.strip():
        return []

    items = [s.strip() for s in string.split(sep) if not ignore_empty or s.strip()]

    if ignore_errors:
        finished = []
        for i in items:
            try:
                finished.append(type_(i))
            except (TypeError, ValueError):
                if not ignore_empty:
                    finished.append(None)

    else:
        finished = [type_(i) if not ignore_empty or i else None for i in items]

    return finished
