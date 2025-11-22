"""
App Manager Service - Manages loading and tracking of mini-apps.
"""

import logging
import json
import os
from pathlib import Path
from typing import Dict, Optional, List
from boss.core.models import App, AppManifest, AppStatus
try:
    # Import secrets manager via flat facade
    from boss.config.secrets_manager import secrets  # type: ignore
except Exception:  # pragma: no cover - fallback if import fails very early
    secrets = None  # type: ignore
from boss.core.interfaces.services import AppManagerService

logger = logging.getLogger(__name__)


class AppManager(AppManagerService):
    """Service for managing mini-apps."""
    
    def __init__(self, apps_directory: Path, event_bus, hardware_service, config, system_default_backend: Optional[str] = None):
        self.apps_directory = apps_directory
        self.event_bus = event_bus
        self.hardware_service = hardware_service
        self.config = config
        # Determine system default screen backend with safe fallbacks
        try:
            if system_default_backend:
                # Prefer explicitly provided backend to avoid reloading config and duplicate logs
                self._system_default_backend = system_default_backend
            elif self.config is not None:
                # Fallback: query config if available
                self._system_default_backend = getattr(self.config.hardware, 'screen_backend', 'rich')
            else:
                self._system_default_backend = 'rich' # Final fallback
        except Exception:
            logger.warning("Could not determine system default screen backend. Falling back to 'rich'.")
            self._system_default_backend = 'rich'
        
        # Internal state
        self._apps = {}
        # Cached lightweight summaries for fast access (number, name, description)
        self._app_summaries_cache = None
        self._app_mappings_file = apps_directory.parent / "config" / "app_mappings.json"
        self._current_app = None
    
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
                    # Validate required_env presence
                    missing = []
                    for env_name in getattr(app.manifest, 'required_env', []) or []:
                        if not env_name:
                            continue
                        present = False
                        if env_name in os.environ:
                            present = True
                        elif secrets is not None:
                            try:
                                if secrets.get(env_name):  # triggers lazy file load once
                                    present = True
                            except Exception:
                                # Conservative: treat as missing if secrets manager errors
                                present = False
                        if not present:
                            missing.append(env_name)
                    if missing:
                        app.mark_error(f"Missing required env vars: {', '.join(missing)}")
                        logger.warning(
                            "App '%s' disabled (missing env): %s", app.manifest.name, ", ".join(missing)
                        )
                    self._apps[app.switch_value] = app
                    loaded_count += 1
                    logger.debug(f"Loaded app: {app.manifest.name} -> switch {app.switch_value}")
            
            except Exception as e:
                logger.error(f"Failed to load app from {app_dir}: {e}")
        
        logger.info(f"Loaded {loaded_count} apps")

        # Build cached summaries (sorted by switch number)
        try:
            summaries: List[Dict] = []
            for switch, app in self._apps.items():
                summaries.append({
                    "number": str(switch).zfill(3),
                    "name": app.manifest.name,
                    "description": getattr(app.manifest, 'description', '') or ''
                })
            summaries.sort(key=lambda x: int(x["number"]))
            self._app_summaries_cache = summaries
            logger.debug("App summaries cache built")
        except Exception as e:
            logger.debug(f"Failed building app summaries cache: {e}")
            self._app_summaries_cache = None
    
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

    def get_app_summaries(self) -> List[Dict]:
        """Return cached list of app summaries: number, name, description."""
        if self._app_summaries_cache is not None:
            # Return a shallow copy to prevent external mutation
            return list(self._app_summaries_cache)

        # Fallback: compute on demand if cache missing
        summaries: List[Dict] = []
        for switch, app in self._apps.items():
            summaries.append({
                "number": str(switch).zfill(3),
                "name": app.manifest.name,
                "description": getattr(app.manifest, 'description', '') or ''
            })
        summaries.sort(key=lambda x: int(x["number"]))
        self._app_summaries_cache = summaries
        return list(self._app_summaries_cache)
    
    def reload_apps(self) -> None:
        """Reload all apps from disk."""
        logger.info("Reloading apps")
        self._apps.clear()
        self._app_summaries_cache = None
        self.load_apps()

    # Simplified: backend switching removed (single textual backend)
    def apply_backend_for_app(self, app: App) -> str:  # compatibility no-op
        return 'textual'

    def restore_backend(self, previous_backend: str) -> None:  # no-op
        return None

    def run_app(self, app: App) -> None:
        """Run an app lifecycle bookkeeping only (execution handled elsewhere)."""
        try:
            app.mark_starting()
            self.event_bus.publish("app.starting", {"app": app.manifest.name}, "app_manager")
            app.mark_running()
            self.event_bus.publish("app.running", {"app": app.manifest.name}, "app_manager")
        except Exception as e:
            app.mark_error(str(e))
            self.event_bus.publish("app.error", {"app": app.manifest.name, "error": str(e)}, "app_manager")
        # No finally block needed; no backend switching anymore
