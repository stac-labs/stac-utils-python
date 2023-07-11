import json
import os
import unittest
from unittest.mock import MagicMock, patch, call

import requests

from src.stac_utils.action_network import ActionnetworkClient


class TestActionnetwork(unittest.TestCase):

    def setUp(self) -> None:
        self.test_client = ActionnetworkClient

    def test_init(self):
        pass

    def test_create_session(self):
        pass

    def test_transform_response(self):
        pass

    def test_check_response_for_rate_limit(self):

        self.assertEqual(1, self.test_check_response_for_rate_limit(None))