"""
Integration tests for BOSS system components.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from pathlib import Path

from boss.core import AppManager, AppRunner, HardwareManager, EventBus, AppAPI


class TestSystemIntegration:
    """Integration tests for BOSS system components."""
    
    def test_app_manager_and_event_bus_integration(self, temp_apps_directory, temp_config_directory):
        """Test AppManager integration with EventBus."""
        event_bus = EventBus()
        event_bus.start()
        
        try:
            app_manager = AppManager(temp_apps_directory, event_bus)
            
            # Mock the config directory path
            app_manager._app_mappings_file = temp_config_directory / "app_mappings.json"
            
            # Load apps
            app_manager.load_apps()
            
            # Verify app was loaded
            assert len(app_manager.get_all_apps()) == 1
            assert app_manager.get_app_by_switch_value(0) is not None
            
        finally:
            event_bus.stop()
    
    def test_hardware_manager_with_mock_factory(self, mock_hardware_factory):
        """Test HardwareManager with mock hardware factory."""
        event_bus = EventBus()
        event_bus.start()
        
        try:
            hardware_manager = HardwareManager(mock_hardware_factory, event_bus)
            hardware_manager.initialize()
            
            # Verify hardware components were created
            assert hardware_manager.buttons is not None
            assert hardware_manager.go_button is not None
            assert hardware_manager.leds is not None
            assert hardware_manager.switches is not None
            assert hardware_manager.display is not None
            assert hardware_manager.screen is not None
            assert hardware_manager.speaker is not None
            
            hardware_manager.cleanup()
            
        finally:
            event_bus.stop()
    
    def test_app_api_integration(self, temp_apps_directory):
        """Test AppAPI integration with event bus."""
        event_bus = EventBus()
        event_bus.start()
        
        try:
            # Create an app API instance
            app_name = "test_app"
            app_path = temp_apps_directory / "test_app"
            
            app_api = AppAPI(event_bus, app_name, app_path)
            
            # Test event bus integration
            handler = Mock()
            subscription_id = app_api.event_bus.subscribe("test_event", handler)
            
            app_api.event_bus.publish("test_event", {"test": "data"})
            time.sleep(0.1)
            
            handler.assert_called_once_with("test_event", {"test": "data"})
            
            # Test logging
            with patch('boss.core.api.logging.getLogger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger
                
                app_api.log_info("Test message")
                mock_logger.info.assert_called_with("Test message")
            
            # Test asset path resolution
            asset_path = app_api.get_asset_path("test.txt")
            expected_path = app_path / "assets" / "test.txt"
            assert asset_path == expected_path
            
        finally:
            event_bus.stop()
    
    def test_app_runner_lifecycle(self, temp_apps_directory, temp_config_directory):
        """Test AppRunner lifecycle management."""
        event_bus = EventBus()
        event_bus.start()
        
        try:
            # Create app manager and load apps
            app_manager = AppManager(temp_apps_directory, event_bus)
            app_manager._app_mappings_file = temp_config_directory / "app_mappings.json"
            app_manager.load_apps()
            
            # Create app API factory
            def create_app_api_factory(app_name: str, app_path: Path) -> AppAPI:
                return AppAPI(event_bus, app_name, app_path)
            
            # Create app runner
            app_runner = AppRunner(event_bus, create_app_api_factory)
            
            # Get the test app
            test_app = app_manager.get_app_by_switch_value(0)
            assert test_app is not None
            
            # Start the app
            app_runner.start_app(test_app)
            time.sleep(0.1)  # Let app start
            
            # Verify app is running
            running_app = app_runner.get_running_app()
            assert running_app == test_app
            assert test_app.is_running
            
            # Stop the app
            app_runner.stop_current_app()
            time.sleep(0.1)  # Let app stop
            
            # Verify app is stopped
            running_app = app_runner.get_running_app()
            assert running_app is None
            assert not test_app.is_running
            
        finally:
            event_bus.stop()
    
    def test_event_flow_integration(self, mock_hardware_factory):
        """Test complete event flow through the system."""
        event_bus = EventBus()
        event_bus.start()
        
        try:
            # Create hardware manager
            hardware_manager = HardwareManager(mock_hardware_factory, event_bus)
            hardware_manager.initialize()
            
            # Set up event monitoring
            events_received = []
            
            def event_handler(event_type, payload):
                events_received.append((event_type, payload))
            
            # Subscribe to various events
            event_bus.subscribe("button_pressed", event_handler)
            event_bus.subscribe("switch_changed", event_handler)
            event_bus.subscribe("led_update", event_handler)
            
            # Simulate hardware events
            event_bus.publish("button_pressed", {"button": "red"})
            event_bus.publish("switch_changed", {"old_value": 0, "new_value": 5})
            event_bus.publish("led_update", {"color": "red", "is_on": True})
            
            time.sleep(0.1)  # Let events process
            
            # Verify events were received
            assert len(events_received) == 3
            assert ("button_pressed", {"button": "red"}) in events_received
            assert ("switch_changed", {"old_value": 0, "new_value": 5}) in events_received
            assert ("led_update", {"color": "red", "is_on": True}) in events_received
            
        finally:
            event_bus.stop()
    
    def test_hardware_state_updates(self, mock_hardware_factory):
        """Test hardware state updates through the system."""
        event_bus = EventBus()
        event_bus.start()
        
        try:
            hardware_manager = HardwareManager(mock_hardware_factory, event_bus)
            hardware_manager.initialize()
            
            # Test LED update
            hardware_manager.update_led("red", True, 0.8)
            # This should work with the mock hardware
            
            # Test display update
            hardware_manager.update_display(123, 1.0)
            # This should work with the mock hardware
            
            # Test screen update
            hardware_manager.update_screen("text", "Hello World", color="white")
            # This should work with the mock hardware
            
            # No exceptions should be raised
            
        finally:
            event_bus.stop()


class TestConfigurationIntegration:
    """Integration tests for configuration loading and validation."""
    
    def test_config_and_app_loading_integration(self, temp_apps_directory, temp_config_directory, mock_config):
        """Test integration between configuration and app loading."""
        event_bus = EventBus()
        
        # Test that app manager can use config to find apps directory
        app_manager = AppManager(temp_apps_directory, event_bus)
        app_manager._app_mappings_file = temp_config_directory / "app_mappings.json"
        
        # Load apps using the configuration
        app_manager.load_apps()
        
        # Verify configuration was used correctly
        assert len(app_manager.get_all_apps()) == 1
        test_app = app_manager.get_app_by_switch_value(0)
        assert test_app is not None
        assert test_app.manifest.name == "Test App"
    
    def test_hardware_config_integration(self, mock_config, mock_hardware_factory):
        """Test hardware configuration integration."""
        event_bus = EventBus()
        
        # Test that hardware manager uses configuration
        hardware_manager = HardwareManager(mock_hardware_factory, event_bus)
        
        # Initialize with the mock factory (which should use the config)
        hardware_manager.initialize()
        
        # Verify hardware was initialized
        assert hardware_manager.buttons is not None
        assert hardware_manager.leds is not None
        assert hardware_manager.display is not None
        
        hardware_manager.cleanup()
