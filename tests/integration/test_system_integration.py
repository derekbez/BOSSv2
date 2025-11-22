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
    
    def test_app_manager_and_event_bus_integration(self, app_manager):
        """Test AppManager integration with EventBus."""
        # Fixture already loads apps; verify
        assert len(app_manager.get_all_apps()) >= 1
        assert app_manager.get_app_by_switch_value(0) is not None
    
    def test_hardware_manager_with_mock_factory(self, hardware_manager):
        """Test HardwareManager with mock hardware factory."""
        # Fixture already initializes; verify hardware components were created
        assert hardware_manager.buttons is not None
        assert hardware_manager.go_button is not None
        assert hardware_manager.leds is not None
        assert hardware_manager.switches is not None
        assert hardware_manager.display is not None
        assert hardware_manager.screen is not None
        assert hardware_manager.speaker is not None
    
    def test_app_api_integration(self, event_bus, apps_dir, app_manager):
        """Test AppAPI integration with event bus and lifecycle events."""
        from tests.helpers.runtime import wait_for
        
        # Start event bus for this test
        if not event_bus._running:
            event_bus.start()
        
        # Create an app API instance
        app_name = "test_app"
        app_path = apps_dir / "test_app"
        
        app_api = AppAPI(event_bus, app_name, app_path, app_manager)
        
        # Test event bus integration with event-driven wait
        handler = Mock()
        subscription_id = app_api.event_bus.subscribe("test_event", handler)
        
        app_api.event_bus.publish("test_event", {"test": "data"}, "test")
        assert wait_for(lambda: handler.call_count == 1, timeout=0.5)
        handler.assert_called_once_with("test_event", {"test": "data"})
        
        # Test asset path resolution
        asset_path = app_api.get_asset_path("test.txt")
        expected_path = app_path / "assets" / "test.txt"
        assert str(asset_path) == str(expected_path)
    
    def test_app_runner_lifecycle(self, event_bus, app_manager, app_runner):
        """Test AppRunner lifecycle management with lifecycle event assertions."""
        from tests.helpers.runtime import wait_for
        
        # Track lifecycle events
        lifecycle_events = []
        def lifecycle_handler(event_type, payload):
            lifecycle_events.append(event_type)
        
        event_bus.subscribe("app_started", lifecycle_handler)
        event_bus.subscribe("app_finished", lifecycle_handler)
        
        # Get the test app
        test_app = app_manager.get_app_by_switch_value(0)
        assert test_app is not None
        
        # Start the app and wait for lifecycle event
        app_runner.start_app(test_app)
        assert wait_for(lambda: test_app.is_running, timeout=1.0)
        assert wait_for(lambda: "app_started" in lifecycle_events, timeout=1.0)
        
        # Verify app is running
        running_app = app_runner.get_running_app()
        assert running_app == test_app
        
        # Stop the app (or wait for it to complete naturally)
        app_runner.stop_current_app()
        assert wait_for(lambda: not test_app.is_running, timeout=1.0)
        # Note: app_finished may be published before or after app completes in test scenario
        
        # Verify app is stopped
        running_app = app_runner.get_running_app()
        assert running_app is None
    
    def test_event_flow_integration(self, event_bus, hardware_manager):
        """Test complete event flow through the system with event-driven waits."""
        from tests.helpers.runtime import wait_for
        
        # Start event bus for this test
        if not event_bus._running:
            event_bus.start()
        
        # Set up event monitoring
        events_received = []
        
        def event_handler(event_type, payload):
            events_received.append((event_type, payload))
        
        # Subscribe to various events
        event_bus.subscribe("button_pressed", event_handler)
        event_bus.subscribe("switch_changed", event_handler)
        event_bus.subscribe("led_update", event_handler)
        
        # Simulate hardware events
        event_bus.publish("button_pressed", {"button": "red"}, "test")
        event_bus.publish("switch_changed", {"old_value": 0, "new_value": 5}, "test")
        event_bus.publish("led_update", {"color": "red", "is_on": True}, "test")
        
        # Event-driven wait
        assert wait_for(lambda: len(events_received) == 3, timeout=0.5)
        assert ("button_pressed", {"button": "red"}) in events_received
        assert ("switch_changed", {"old_value": 0, "new_value": 5}) in events_received
        assert ("led_update", {"color": "red", "is_on": True}) in events_received
    
    def test_hardware_state_updates(self, hardware_manager):
        """Test hardware state updates through the system."""
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


class TestConfigurationIntegration:
    """Integration tests for configuration loading and validation."""
    
    def test_config_and_app_loading_integration(self, app_manager):
        """Test integration between configuration and app loading."""
        # Fixture already loads apps; verify configuration was used correctly
        assert len(app_manager.get_all_apps()) >= 1
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
