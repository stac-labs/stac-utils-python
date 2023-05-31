import filecmp
import unittest

from unittest.mock import patch
from enum import Enum

from src.stac_utils.secret_factory import SecretsJSONFactory


class TestSecretFactory(unittest.TestCase):
    def test_build_input_string(self):
        """Test that secrets factory can build correct input strings"""

        class ThisInput(Enum):
            TEST_SCHEMA = {"name": "FOO", "is_required": True}

        secrets = SecretsJSONFactory("test", ThisInput)
        self.assertEqual(
            "Enter INPUT1 (required):",
            secrets.build_input_string(
                {
                    "name": "INPUT1",
                    "is_required": True,
                }
            ),
        )
        self.assertEqual(
            "Enter INPUT2 (not required, hit enter to continue):",
            secrets.build_input_string(
                {
                    "name": "INPUT2",
                    "is_required": False,
                }
            ),
        )
        self.assertEqual(
            "Enter INPUT3 (not required, hit enter to continue):",
            secrets.build_input_string(
                {"name": "INPUT3", "is_required": True}, is_override_mode=True
            ),
        )

    @patch("src.stac_utils.secret_factory.input", create=True)
    def test_required_input(self, mocked_input):
        """Test non-response entry for required input"""

        class ThisInput(Enum):
            TEST_SCHEMA = {"name": "TEST_SCHEMA", "is_required": True}

        mocked_input.side_effect = ["", "", "demsspsp.commons"]

        secrets = SecretsJSONFactory("test", ThisInput)
        secrets.build_json()
        self.assertDictEqual({"TEST_SCHEMA": "demsspsp.commons"}, secrets.json)

    @patch("src.stac_utils.secret_factory.input", create=True)
    def test_optional_input(self, mocked_input):
        """Test non-response entry for optional input"""

        class ThisInput(Enum):
            TEST_OPTION = {"name": "TEST_OPTION", "is_required": False}

        mocked_input.side_effect = [""]

        secrets = SecretsJSONFactory("test", ThisInput)
        secrets.build_json()
        self.assertDictEqual({}, secrets.json)

    @patch("src.stac_utils.secret_factory.input", create=True)
    def test_json_input(self, mocked_input):
        """Test that JSON inputs are converted to JSON string"""

        class ThisInput(Enum):
            TEST_SERVICE_ACCOUNT = {
                "name": "TEST_SERVICE_ACCOUNT",
                "is_required": True,
                "is_json_string": True,
            }

        mocked_input.side_effect = ['{"FOO": "BAR"}']

        optional_secrets = SecretsJSONFactory("test", ThisInput)
        optional_secrets.build_json()
        self.assertDictEqual(
            {"TEST_SERVICE_ACCOUNT": '{"FOO": "BAR"}'}, optional_secrets.json
        )

    @patch("src.stac_utils.secret_factory.input", create=True)
    def test_optional_override(self, mocked_input):
        """Test non-response entry for optional override input"""

        class ThisInput(Enum):
            TEST_OVERRIDES = {
                "name": "TEST_OVERRIDES",
                "is_required": False,
                "is_overridable": False,
                "is_overrider": True,
            }

        mocked_input.side_effect = [""]

        secrets = SecretsJSONFactory("test", ThisInput)
        secrets.build_json()
        self.assertDictEqual({}, secrets.json)

    @patch("src.stac_utils.secret_factory.input", create=True)
    def test_handle_overridable(self, mocked_input):
        """Test that override mode handles is_overridable and is_overrider"""

        class ThisInput(Enum):
            TEST_ID = {"name": "TEST_ID", "is_required": True, "is_overridable": True}
            TEST_OPTION = {
                "name": "TEST_OPTION",
                "is_required": False,
                "is_overridable": True,
            }
            TEST_OVERRIDES = {
                "name": "TEST_OVERRIDES",
                "is_required": False,
                "is_overridable": False,
                "is_overrider": True,
            }

        mocked_input.side_effect = ["1234", "", "y", "1234", "", "an option", ""]

        secrets = SecretsJSONFactory("test", ThisInput)
        secrets.build_json()
        self.assertDictEqual(
            {
                "TEST_ID": "1234",
                "TEST_OVERRIDES": '{"1234": {"TEST_OPTION": "an option"}}',
            },
            secrets.json,
        )

    @patch("src.stac_utils.secret_factory.input", create=True)
    def test_handle_required_in_overrides(self, mocked_input):
        """Test that required inputs are not required in override mode"""

        class ThisInput(Enum):
            TEST_SCHEMA = {
                "name": "TEST_SCHEMA",
                "is_required": True,
                "is_overridable": False,
            }
            TEST_OPTION = {
                "name": "TEST_OPTION",
                "is_required": False,
                "is_overridable": True,
            }
            TEST_OVERRIDES = {
                "name": "TEST_OVERRIDES",
                "is_required": True,
                "is_overridable": False,
                "is_overrider": True,
            }

        mocked_input.side_effect = ["demsspsp.commons", "", "1234", "an option", ""]

        secrets = SecretsJSONFactory("test", ThisInput)
        secrets.build_json()
        self.assertDictEqual(
            {
                "TEST_SCHEMA": "demsspsp.commons",
                "TEST_OVERRIDES": '{"1234": {"TEST_OPTION": "an option"}}',
            },
            secrets.json,
        )

    @patch("src.stac_utils.secret_factory.input", create=True)
    def test_handle_json_in_overrides(self, mocked_input):
        """Test that override mode correctly handles JSON inputs"""

        class ThisInput(Enum):
            TEST_SERVICE_ACCOUNT = {
                "name": "TEST_SERVICE_ACCOUNT",
                "is_required": False,
                "is_overridable": True,
                "is_json_string": True,
            }
            TEST_OVERRIDES = {
                "name": "TEST_OVERRIDES",
                "is_required": False,
                "is_overridable": False,
                "is_overrider": True,
            }

        mocked_input.side_effect = ["", "y", "1234", '{"FOO": "BAR"}', ""]

        secrets = SecretsJSONFactory("test", ThisInput)
        secrets.build_json()
        self.assertDictEqual(
            {
                "TEST_OVERRIDES": '{"1234": {"TEST_SERVICE_ACCOUNT": "{\\"FOO\\": \\"BAR\\"}"}}'
            },
            secrets.json,
        )

    @patch("src.stac_utils.secret_factory.input", create=True)
    def test_write_json(self, mocked_input):
        """Test that the secrets JSON writes correctly"""

        class ThisInput(Enum):
            TEST_SCHEMA = {"name": "FOO", "is_required": True}

        mocked_input.side_effect = ["BAR"]

        secrets = SecretsJSONFactory("test", ThisInput)
        secrets.build_json()
        secrets.write_json()
        self.assertTrue(
            filecmp.cmp("src/tests/mock-credentials.json", "secrets-test.json")
        )


if __name__ == "__main__":
    unittest.main()
