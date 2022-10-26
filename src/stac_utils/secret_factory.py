import json
import readline # necessary to support service account length inputs

from enum import Enum
from src.stac_utils.truthy import truthy

class SecretsJSONFactory:
    def __init__(self, secret_name: str, json_inputs: Enum):
        self.filename = "secrets-{}.json".format(secret_name)
        self.json_inputs = json_inputs
        self.json = {}

    def build_json(self):
        """
            Creates secrets JSON from inputs enum, which contains a dict of:
            * "name" (str, required)
            * "is_required" (bool, required)
            * "is_overridable" (bool, required)
            * "is_json_string") (bool, optional, eg for service accounts)
            * "is_overrider" (bool, optional, for setting session-specific overrides)
        """
        for json_input in self.json_inputs:
            input_settings = json_input.value
            is_required = input_settings.get("is_required")

            if input_settings.get("is_overrider"):
                if not is_required:
                    is_add_overrides = input(
                        f"Add overrides by {input_settings.get('name')}?"
                    )
                    if not truthy(is_add_overrides):
                        continue
                
                response = self.build_overrider(input_settings)

            else:
                response = input(
                    self.build_input_string(input_settings)
                )
                
                while response == "" and is_required:
                    response = input("Try again:")
                if response == "" and not is_required:
                    continue

                if input_settings.get("is_json_string"):
                    response = json.dumps(json.loads(response, strict=False))

            self.json[input_settings.get("name")] = response
    
    def build_overrider(self, input_settings: dict) -> str:
        """Builds a JSON string with overrides for each committee/county/whatever"""
        override_json = {}
        while True:
            override_name = input(
                f"New override {input_settings.get('name')} ID (hit enter if done):"
            )
            if override_name == "":
                break

            this_override = {}
            for json_input in self.json_inputs:
                input_settings = json_input.value

                if (
                    input_settings.get("is_overrider") or
                    not input_settings.get("is_overridable")
                ):
                    continue
                response = input(
                    self.build_input_string(input_settings, is_override_mode=True)
                )

                if response == "":
                    continue

                if input_settings.get("is_json_string"):
                    response = json.dumps(json.loads(response, strict=False))
                
                this_override[input_settings.get("name")] = response
            override_json[override_name] = this_override

        return json.dumps(override_json)
    
    def build_input_string(self, input_settings: dict, is_override_mode = False) -> str:
        input_string = f"Enter {input_settings.get('name')}"

        if input_settings.get("is_required") and not is_override_mode:
            input_string += " (required):"
        else:
            input_string += " (not required, hit enter to continue):"
        
        return input_string
    
    def write_json(self):
        with open(self.filename, "w") as outfile:
            json.dump(self.json, outfile)