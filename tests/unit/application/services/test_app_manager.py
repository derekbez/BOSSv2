"""
Unit tests for AppManager service.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from boss.application.services.app_manager import AppManager
from boss.domain.models.app import App, AppManifest


class TestAppManager:
    """Test cases for AppManager service."""
    
    def test_init(self, mock_event_bus, tmp_path):
        """Test AppManager initialization."""
        apps_dir = tmp_path / "apps"
        apps_dir.mkdir()
        
        app_manager = AppManager(apps_dir, mock_event_bus)
        
        assert app_manager.apps_directory == apps_dir
        assert app_manager.event_bus == mock_event_bus
        assert app_manager._apps == {}
        assert app_manager._current_app is None
    
    def test_load_app_mappings_with_nested_structure(self, mock_event_bus, tmp_path):
        """Test loading app mappings with nested JSON structure."""
        apps_dir = tmp_path / "apps"
        apps_dir.mkdir()
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        # Create app mappings file with nested structure
        mappings_file = config_dir / "app_mappings.json"
        mappings_data = {
            "app_mappings": {
                "0": "list_all_apps",
                "1": "hello_world"
            },
            "parameters": {}
        }
        mappings_file.write_text(json.dumps(mappings_data))
        
        app_manager = AppManager(apps_dir, mock_event_bus)
        
        # Manually set the mappings file path for test
        app_manager._app_mappings_file = mappings_file
        
        mappings = app_manager._load_app_mappings()
        
        assert mappings == {"0": "list_all_apps", "1": "hello_world"}
    
    def test_load_app_mappings_with_flat_structure(self, mock_event_bus, tmp_path):
        """Test loading app mappings with flat JSON structure."""
        apps_dir = tmp_path / "apps"
        apps_dir.mkdir()
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        # Create app mappings file with flat structure
        mappings_file = config_dir / "app_mappings.json"
        mappings_data = {
            "0": "list_all_apps",
            "1": "hello_world"
        }
        mappings_file.write_text(json.dumps(mappings_data))
        
        app_manager = AppManager(apps_dir, mock_event_bus)
        app_manager._app_mappings_file = mappings_file
        
        mappings = app_manager._load_app_mappings()
        
        assert mappings == {"0": "list_all_apps", "1": "hello_world"}
    
    def test_load_app_mappings_file_not_found(self, mock_event_bus, tmp_path):
        """Test loading app mappings when file doesn't exist."""
        apps_dir = tmp_path / "apps"
        apps_dir.mkdir()
        
        app_manager = AppManager(apps_dir, mock_event_bus)
        app_manager._app_mappings_file = tmp_path / "nonexistent.json"
        
        mappings = app_manager._load_app_mappings()
        
        assert mappings == {}
    
    def test_load_app_with_standard_manifest(self, mock_event_bus, tmp_path):
        """Test loading an app with standard manifest format."""
        apps_dir = tmp_path / "apps"
        apps_dir.mkdir()
        app_dir = apps_dir / "test_app"
        app_dir.mkdir()
        
        # Create standard format manifest
        manifest_data = {
            "name": "Test App",
            "description": "A test application",
            "version": "1.0.0",
            "author": "Test Author",
            "entry_point": "main.py",
            "timeout_seconds": 60,
            "requires_network": False,
            "requires_audio": False,
            "tags": ["test"]
        }
        manifest_file = app_dir / "manifest.json"
        manifest_file.write_text(json.dumps(manifest_data))
        
        # Create main.py
        main_file = app_dir / "main.py"
        main_file.write_text("def run(stop_event, api): pass")
        
        app_manager = AppManager(apps_dir, mock_event_bus)
        mappings = {"0": "test_app"}
        
        app = app_manager._load_app(app_dir, mappings)
        
        assert app is not None
        assert app.switch_value == 0
        assert app.manifest.name == "Test App"
        assert app.manifest.description == "A test application"
        assert app.app_path == app_dir
    
    def test_load_app_with_legacy_manifest(self, mock_event_bus, tmp_path):
        """Test loading an app with legacy manifest format."""
        apps_dir = tmp_path / "apps"
        apps_dir.mkdir()
        app_dir = apps_dir / "test_app"
        app_dir.mkdir()
        
        # Create legacy format manifest
        manifest_data = {
            "id": "test_app",
            "title": "Test App Title",
            "description": "A test application",
            "entry_point": "main.py",
            "config": {"some": "config"}
        }
        manifest_file = app_dir / "manifest.json"
        manifest_file.write_text(json.dumps(manifest_data))
        
        # Create main.py
        main_file = app_dir / "main.py"
        main_file.write_text("def run(stop_event, api): pass")
        
        app_manager = AppManager(apps_dir, mock_event_bus)
        mappings = {"0": "test_app"}
        
        app = app_manager._load_app(app_dir, mappings)
        
        assert app is not None
        assert app.switch_value == 0
        assert app.manifest.name == "Test App Title"  # title mapped to name
        assert app.manifest.version == "1.0.0"  # default added
        assert app.manifest.author == "Unknown"  # default added
    
    def test_load_app_no_mapping(self, mock_event_bus, tmp_path):
        """Test loading an app with no switch mapping."""
        apps_dir = tmp_path / "apps"
        apps_dir.mkdir()
        app_dir = apps_dir / "unmapped_app"
        app_dir.mkdir()
        
        # Create manifest
        manifest_data = {
            "name": "Unmapped App",
            "description": "An unmapped application",
            "version": "1.0.0",
            "author": "Test Author"
        }
        manifest_file = app_dir / "manifest.json"
        manifest_file.write_text(json.dumps(manifest_data))
        
        # Create main.py
        main_file = app_dir / "main.py"
        main_file.write_text("def run(stop_event, api): pass")
        
        app_manager = AppManager(apps_dir, mock_event_bus)
        mappings = {"0": "other_app"}  # Different app mapped
        
        app = app_manager._load_app(app_dir, mappings)
        
        assert app is None  # Should return None for unmapped apps
    
    def test_load_apps_integration(self, mock_event_bus, temp_apps_directory):
        """Test loading apps integration."""
        app_manager = AppManager(temp_apps_directory, mock_event_bus)
        
        # Mock the mappings file path
        config_dir = temp_apps_directory.parent / "config"
        config_dir.mkdir(exist_ok=True)
        mappings_file = config_dir / "app_mappings.json"
        mappings_data = {
            "app_mappings": {
                "0": "test_app"
            },
            "parameters": {}
        }
        mappings_file.write_text(json.dumps(mappings_data))
        app_manager._app_mappings_file = mappings_file
        
        app_manager.load_apps()
        
        assert len(app_manager._apps) == 1
        assert 0 in app_manager._apps
        assert app_manager._apps[0].manifest.name == "Test App"
    
    def test_get_app_by_switch_value(self, mock_event_bus, tmp_path):
        """Test getting app by switch value."""
        apps_dir = tmp_path / "apps"
        apps_dir.mkdir()
        
        app_manager = AppManager(apps_dir, mock_event_bus)
        
        # Create mock app
        mock_app = Mock(spec=App)
        app_manager._apps[42] = mock_app
        
        result = app_manager.get_app_by_switch_value(42)
        assert result == mock_app
        
        result = app_manager.get_app_by_switch_value(99)
        assert result is None
    
    def test_get_all_apps(self, mock_event_bus, tmp_path):
        """Test getting all apps."""
        apps_dir = tmp_path / "apps"
        apps_dir.mkdir()
        
        app_manager = AppManager(apps_dir, mock_event_bus)
        
        # Create mock apps
        mock_app1 = Mock(spec=App)
        mock_app2 = Mock(spec=App)
        app_manager._apps = {1: mock_app1, 2: mock_app2}
        
        result = app_manager.get_all_apps()
        
        assert result == {1: mock_app1, 2: mock_app2}
        assert result is not app_manager._apps  # Should be a copy
    
    def test_current_app_management(self, mock_event_bus, tmp_path):
        """Test current app get/set functionality."""
        apps_dir = tmp_path / "apps"
        apps_dir.mkdir()
        
        app_manager = AppManager(apps_dir, mock_event_bus)
        
        assert app_manager.get_current_app() is None
        
        mock_app = Mock(spec=App)
        app_manager.set_current_app(mock_app)
        
        assert app_manager.get_current_app() == mock_app
        
        app_manager.set_current_app(None)
        assert app_manager.get_current_app() is None
