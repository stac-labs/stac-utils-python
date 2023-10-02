import os
import unittest
from unittest.mock import MagicMock, patch

import psycopg

from stac_utils.google import send_data_to_sheets
from src.stac_utils.database_utils import (
    make_postgres_connection,
    run_postgres_query,
    postgres_to_google_sheets,
)


class TestDatabaseUtils(unittest.TestCase):
    def test_make_postgres_connection(self):
        pass
