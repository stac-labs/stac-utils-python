import pandas as pd

from .google import send_data_to_sheets


def send_dataframe_to_sheets(
    df: pd.DataFrame,
    spreadsheet_id: str,
    range: str,
    input_option: str = "RAW",
    client=None,
) -> dict:
    """Posts the DataFrame to the Google Sheet and returns the API response"""

    data = transform_to_lists(df)
    return send_data_to_sheets(data, spreadsheet_id, range, input_option, client)


def transform_to_lists(df: pd.DataFrame) -> list[list]:
    df = df.fillna("")
    row_data = [[col for col in df.columns]]
    for row in df.itertuples(index=False):
        row_data.append([str(col) for col in row])
    return row_data
