def listify(
    string: str,
    type_: type = str,
    sep: str = ",",
    ignore_errors: bool = False,
    ignore_empty: bool = True,
) -> list:
    """
    Split a string into a list, converting to a type as necessary. For example, `"foo, bar, spam"` will become `["foo","bar","spam"]`.

    :param string: String to split into list
    :param type_: Type to convert, if desired, `str` by default
    :param sep: Separator for list
    :param ignore_errors: `False` by default
    :param ignore_empty: `True` by default
    :return: String converted to list
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
