def convert_to_eid(id: int) -> str:
    """
    Convert an ID, such as a VAN ID or an export request ID, into an EID string.
    Useful for creating direct links to VoteBuilder.
    :param id: ID number to convert
    :return: EID
    """
    ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    reverse_hex_id = f"{id:x}"[::-1]
    letter = ALPHABET[id % 17]

    return f"EID{reverse_hex_id}{letter}".upper()
