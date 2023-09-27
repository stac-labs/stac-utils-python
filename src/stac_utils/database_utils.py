import os

import psycopg

from stac_utils.google import send_data_to_sheets
from stac_utils import listify


def make_postgresql_connection(
    pg_host: str = None,
    pg_db: str = None,
    pg_user: str = None,
    pg_pw: str = None,
    pg_port: int = None,
) -> psycopg.Connection:
    host = pg_host or os.environ["PG_HOST"]
    dbname = pg_db or os.environ["PG_DB"]
    user = pg_user or os.environ["PG_USER"]
    password = pg_pw or os.environ.get("PG_PW")
    port = pg_port or os.environ.get("PG_PORT", 5432)
    engine = psycopg.connect(
        dbname=dbname, user=user, password=password, host=host, port=port
    )

    return engine


def run_query(engine: psycopg.Connection, sql: str) -> list[list]:
    data = []
    with engine.cursor() as cursor:
        cursor.execute(sql)
        for row in cursor.fetchall():
            row = [str(value) if value is not None else "" for value in row]
            data.append(row)
    return data


def run_database_to_sheets():
    google_sheet_id = os.environ["GOOGLE_SHEET_ID"]
    sheet_range = os.environ["GOOGLE_SHEET_RANGE"]
    sheet_headers = listify(os.environ["GOOGLE_SHEET_HEADERS"])

    sql_query = os.environ["SQL_QUERY"]
    engine = make_postgresql_connection()
    data = run_query(engine, sql_query)
    send_data_to_sheets([sheet_headers] + data, google_sheet_id, sheet_range)