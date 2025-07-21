
"""
ConfigManager: Loads and validates configuration from a JSON file (app_mappings.json)
"""
import json
from typing import Any, Dict
from boss.core.paths import CONFIG_PATH

import os

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

    @property
    def app_mappings(self) -> Dict[str, Any]:
        """
        Expose app_mappings as a property for consistent access.
        Returns a dict mapping switch values (as str) to app info.
        """
        return self.config.get("app_mappings", {})

    @app_mappings.setter
    def app_mappings(self, value: Dict[str, Any]):
        self.config["app_mappings"] = value
        self.save()

    def get_app_for_value(self, value: int):
        return self.app_mappings.get(str(value))

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

    def get_manifest(self, app_dir: str) -> dict:
        """
        Load and return the manifest.json for a given app directory.
        Returns an empty dict if not found or invalid.
        """
        from boss.core.paths import APPS_DIR
        import os
        import json
        manifest_path = os.path.join(APPS_DIR, app_dir, 'manifest.json')
        if not os.path.exists(manifest_path):
            return {}
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}