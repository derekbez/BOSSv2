"""Test the AppAPI asset path methods."""

import pytest
from pathlib import Path
from unittest.mock import Mock

from boss.application.api.app_api import AppAPI


class TestAppAPIAssetPaths:
    """Test asset path methods in AppAPI."""
    
    def test_get_asset_path_returns_full_file_path(self):
        """Test that get_asset_path returns full path to specific file."""
        mock_event_bus = Mock()
        app_path = Path("/test/app/path")
        api = AppAPI(mock_event_bus, "test_app", app_path)
        
        result = api.get_asset_path("test.json")
        expected = "/test/app/path/assets/test.json"
        
        assert result == expected
    
    def test_get_app_asset_path_returns_assets_directory(self):
        """Test that get_app_asset_path returns assets directory path."""
        mock_event_bus = Mock()
        app_path = Path("/test/app/path")
        api = AppAPI(mock_event_bus, "test_app", app_path)
        
        result = api.get_app_asset_path()
        expected = "/test/app/path/assets"
        
        assert result == expected
    
    def test_both_methods_work_together(self):
        """Test that both asset path methods work correctly together."""
        mock_event_bus = Mock()
        app_path = Path("/test/different/path")
        api = AppAPI(mock_event_bus, "test_app", app_path)
        
        # Get assets directory
        assets_dir = api.get_app_asset_path()
        assert assets_dir == "/test/different/path/assets"
        
        # Get specific file path
        file_path = api.get_asset_path("data.json")
        assert file_path == "/test/different/path/assets/data.json"
        
        # The file path should start with the assets directory
        assert file_path.startswith(assets_dir)