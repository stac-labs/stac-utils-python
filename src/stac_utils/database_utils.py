import os

import psycopg

from stac_utils.google import send_data_to_sheets


def make_postgres_connection(
    pg_host: str = None,
    pg_db: str = None,
    pg_user: str = None,
    pg_pw: str = None,
    pg_port: int = None,
) -> psycopg.Connection:
    """
    Makes a connection with a Postgres database and returns engine

    :param pg_host: Host for Postgres database
    :param pg_db: Postgres database name
    :param pg_user: Postgres database username
    :param pg_pw: Postgres database password
    :param pg_port: Postgres database port, defaults to `5432`
    :return: engine
    """
    host = pg_host or os.environ["PG_HOST"]
    dbname = pg_db or os.environ["PG_DB"]
    user = pg_user or os.environ["PG_USER"]
    password = pg_pw or os.environ.get("PG_PW")
    port = pg_port or os.environ.get("PG_PORT", 5432)
    engine = psycopg.connect(
        dbname=dbname, user=user, password=password, host=host, port=port
    )

    return engine


def run_postgres_query(engine: psycopg.Connection, sql: str) -> list[list]:
    """
    Given Postgres connection, runs SQL query on database and returns results

    :param engine: Engine for Postgres database connection
    :param sql: SQL query to run
    :return: Results of SQL query as list of lists
    """
    data = []
    with engine.cursor() as cursor:
        cursor.execute(sql)
        for row in cursor.fetchall():
            row = [str(value) if value is not None else "" for value in row]
            data.append(row)
    return data


def postgres_to_google_sheets(
    google_sheet_id: str,
    google_sheet_range: str,
    google_sheet_headers: list[str],
    sql_query: str,
    engine: psycopg.Connection = None,
):
    """
    Establishes Postgres database connection, runs query, and sends query results to Google sheet

    :param google_sheet_id: ID of destination Google sheet
    :param google_sheet_range: Range in destination Google sheet
    :param google_sheet_headers: Headers for destination Google sheet
    :param sql_query: SQL query to run
    :param engine: Postgres database connection
    """

    engine = engine or make_postgres_connection()
    data = run_postgres_query(engine, sql_query)
    send_data_to_sheets(
        [google_sheet_headers] + data, google_sheet_id, google_sheet_range
    )
