import pandas as pd

from .google import send_data_to_sheets


def send_dataframe_to_sheets(
    df: pd.DataFrame,
    spreadsheet_id: str,
    range: str,
    input_option: str = "RAW",
    client=None,
) -> dict:
    """
    Posts the DataFrame to the Google Sheet and returns the API response

    :param df: Specified Pandas DataFrame
    :param spreadsheet_id: Google Sheets spreadsheet ID
    :param range: Specified range within sheet
    :param input_option: Defaults to `RAW`
    :param client: Google Sheets client
    :return: API response
    """

    data = transform_to_lists(df)
    return send_data_to_sheets(data, spreadsheet_id, range, input_option, client)


def transform_to_lists(df: pd.DataFrame) -> list[list]:
    """
    Transforms given Pandas DataFrame into list of lists

    :param df: Given Pandas DataFrame
    :return: Data from specified DataFrame as list of lists
    """
    df = df.fillna("")
    row_data = [[col for col in df.columns]]
    for row in df.itertuples(index=False):
        row_data.append([str(col) for col in row])
    return row_data
