import pandas as pd
import io

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


def get_dataframe_from_text_stream(
    data: io.StringIO, delimiter: str, header=1
) -> pd.DataFrame:
    """
    Convert a text stream into a pandas DataFrame. Columns edited for BigQuery upload.

    :param data: text stream
    :param delimiter: The delimiter for your file, will usually be a comma
    :param header: 1 if there is a header in your file, 0 if no header in your file. Defaults to 1
    :return: Pandas Dataframe for upload into BQ
    """

    # get number of max rows of data
    column_length_list = [len(i.split(delimiter)) for i in data.readlines()]
    number_of_columns = int(max(column_length_list))

    # back to start of stream
    data.seek(0)

    # names parameter will handle cases where data spills over to non-named columns
    df = pd.read_csv(data, sep=delimiter, dtype=object, names=range(number_of_columns))

    # handle header, if exists
    if header == 0:
        df.columns = [f"Col_{i}" for i in range(number_of_columns)]
    else:
        # set column_names from first row, and handle NaN columns
        df.columns = df.iloc[0]
        df = df[1:]
        df = df.reset_index(drop=True)

        # rename unnamed columns
        cols = pd.Series(df.columns)
        cols = cols.fillna(
            "Unnamed_" + (cols.groupby(cols.isnull()).cumcount() + 1).astype(str)
        )
        df.columns = cols

    # format column names to bq specifications
    df.columns = df.columns.str.replace("[^A-Za-z0-9_]", "_", regex=True)
    df.columns = df.columns.str.replace("^[0-9]", "_", regex=True)

    return df
