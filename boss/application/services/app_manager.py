"""
App Manager Service - Manages loading and tracking of mini-apps.
"""

import logging
import json
from pathlib import Path
from typing import Dict, Optional, List
from boss.domain.models.app import App, AppManifest, AppStatus
from boss.domain.interfaces.services import AppManagerService

logger = logging.getLogger(__name__)


class AppManager(AppManagerService):
    """Service for managing mini-apps."""
    
    def __init__(self, apps_directory: Path, event_bus):
        self.apps_directory = apps_directory
        self.event_bus = event_bus
        self._apps: Dict[int, App] = {}
        self._app_mappings_file = apps_directory.parent / "config" / "app_mappings.json"
        self._current_app: Optional[App] = None
    
    def load_apps(self) -> None:
        """Load all available apps from the apps directory and mappings file."""
        logger.info(f"Loading apps from {self.apps_directory}")
        
        # Load app mappings
        mappings = self._load_app_mappings()
        
        # Scan for app directories
        if not self.apps_directory.exists():
            logger.warning(f"Apps directory does not exist: {self.apps_directory}")
            return
        
        loaded_count = 0
        for app_dir in self.apps_directory.iterdir():
            if not app_dir.is_dir() or app_dir.name.startswith('.') or app_dir.name.startswith('_'):
                continue
            
            try:
                app = self._load_app(app_dir, mappings)
                if app:
                    self._apps[app.switch_value] = app
                    loaded_count += 1
                    logger.debug(f"Loaded app: {app.manifest.name} -> switch {app.switch_value}")
            
            except Exception as e:
                logger.error(f"Failed to load app from {app_dir}: {e}")
        
        logger.info(f"Loaded {loaded_count} apps")
    
    def get_app_by_switch_value(self, switch_value: int) -> Optional[App]:
        """Get the app mapped to a switch value."""
        return self._apps.get(switch_value)
    
    def get_all_apps(self) -> Dict[int, App]:
        """Get all loaded apps."""
        return self._apps.copy()
    
    def get_current_app(self) -> Optional[App]:
        """Get the currently running app."""
        return self._current_app
    
    def set_current_app(self, app: Optional[App]) -> None:
        """Set the currently running app."""
        self._current_app = app
    
    def _load_app_mappings(self) -> Dict[str, str]:
        """Load switch-to-app mappings from JSON file."""
        try:
            if self._app_mappings_file.exists():
                with open(self._app_mappings_file, 'r') as f:
                    data = json.load(f)
                    # Handle nested structure with "app_mappings" key
                    if isinstance(data, dict) and "app_mappings" in data:
                        return data["app_mappings"]
                    else:
                        return data
            else:
                logger.warning(f"App mappings file not found: {self._app_mappings_file}")
                return {}
        except Exception as e:
            logger.error(f"Error loading app mappings: {e}")
            return {}
    
    def _load_app(self, app_dir: Path, mappings: Dict[str, str]) -> Optional[App]:
        """Load a single app from its directory."""
        app_name = app_dir.name
        
        # Find switch value by looking for this app name in the mappings values
        switch_value = None
        for switch_str, mapped_app_name in mappings.items():
            if mapped_app_name == app_name:
                try:
                    switch_value = int(switch_str)
                    break
                except ValueError:
                    logger.warning(f"Invalid switch value in mappings: {switch_str}")
                    continue
        
        if switch_value is None:
            logger.warning(f"No switch mapping found for app: {app_name}")
            return None
        
        # Load manifest
        manifest_file = app_dir / "manifest.json"
        if not manifest_file.exists():
            logger.warning(f"No manifest.json found for app: {app_name}")
            return None
        
        try:
            manifest = AppManifest.from_file(manifest_file)
        except Exception as e:
            logger.error(f"Invalid manifest for app {app_name}: {e}")
            return None
        
        # Create app instance
        try:
            app = App(
                switch_value=switch_value,
                manifest=manifest,
                app_path=app_dir
            )
            return app
        except Exception as e:
            logger.error(f"Invalid app configuration for {app_name}: {e}")
            return None
    
    def get_app_list(self) -> List[Dict]:
        """Get a list of all apps for external interfaces."""
        return [app.to_dict() for app in self._apps.values()]
    
    def reload_apps(self) -> None:
        """Reload all apps from disk."""
        logger.info("Reloading apps")
        self._apps.clear()
        self.load_apps()
