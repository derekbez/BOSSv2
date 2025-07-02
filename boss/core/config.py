"""
ConfigManager: Loads and validates configuration from a JSON file (BOSSsettings.json)
"""
import json
from typing import Any, Dict
from boss.core.paths import CONFIG_PATH

class ConfigManager:
    def __init__(self, config_path: str = CONFIG_PATH):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load()

    def load(self):
        if not os.path.exists(self.config_path):
            self.config = {"app_mappings": {}, "parameters": {}}
            self.save()
        else:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)

    def save(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get_app_for_value(self, value: int):
        return self.config.get("app_mappings", {}).get(str(value))

    def set_app_mapping(self, value: int, app_name: str, params: dict = None):
        if "app_mappings" not in self.config:
            self.config["app_mappings"] = {}
        self.config["app_mappings"][str(value)] = {"app": app_name, "params": params or {}}
        self.save()

    def validate(self) -> bool:
        # Basic validation: check required keys
        if not isinstance(self.config, dict):
            return False
        if "app_mappings" not in self.config:
            return False
        return True
