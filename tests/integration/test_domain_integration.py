"""
Integration tests for domain models and system components.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from boss.core.models import App, AppManifest, AppStatus
from boss.core import SystemManager, EventBus


class TestDomainModelIntegration:
    """Integration tests for domain models."""
    
    def test_app_manifest_loading_integration(self, temp_apps_directory):
        """Test complete app manifest loading from file."""
        app_dir = temp_apps_directory / "test_app"
        
        # Create a manifest with legacy format
        legacy_manifest = {
            "id": "legacy_app",
            "title": "Legacy Test App", 
            "description": "A legacy format test app"
        }
        
        import json
        manifest_path = app_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(legacy_manifest, f)
        
        # Load manifest using the class method
        manifest = AppManifest.from_file(manifest_path)
        
        # Verify conversion from legacy format
        assert manifest.name == "Legacy Test App"
        assert manifest.description == "A legacy format test app"
        assert manifest.version == "1.0.0"  # Default value
        assert manifest.author == "Unknown"  # Default value
        assert manifest.entry_point == "main.py"  # Default value
    
    def test_app_lifecycle_integration(self, temp_apps_directory):
        """Test complete app lifecycle from creation to error state."""
        app_dir = temp_apps_directory / "test_app"
        
        # Load manifest
        manifest_path = app_dir / "manifest.json"
        manifest = AppManifest.from_file(manifest_path)
        
        # Create app
        app = App(
            switch_value=42,
            manifest=manifest,
            app_path=app_dir
        )
        
        # Test initial state
        assert app.status == AppStatus.STOPPED
        assert not app.is_running
        assert app.can_start
        
        # Test starting
        app.mark_starting()
        assert app.status == AppStatus.STARTING
        assert app.is_running
        assert not app.can_start
        
        # Test running
        app.mark_running()
        assert app.status == AppStatus.RUNNING
        assert app.is_running
        
        # Test stopping
        app.mark_stopping()
        assert app.status == AppStatus.STOPPING
        
        # Test stopped
        app.mark_stopped()
        assert app.status == AppStatus.STOPPED
        assert not app.is_running
        assert app.can_start
        
        # Test error state
        app.mark_error("Test error")
        assert app.status == AppStatus.ERROR
        assert app.error_message == "Test error"
        assert not app.is_running
        assert app.can_start  # Can restart from error
    
    def test_app_validation_integration(self, temp_config_directory):
        """Test app validation with various invalid configurations."""
        # Test invalid switch value
        with pytest.raises(ValueError, match="Switch value must be 0-255"):
            App(
                switch_value=256,  # Invalid
                manifest=AppManifest(
                    name="Test",
                    description="Test",
                    version="1.0",
                    author="Test"
                ),
                app_path=temp_config_directory  # Valid path
            )
        
        # Test non-existent app path
        with pytest.raises(ValueError, match="App path does not exist"):
            App(
                switch_value=1,
                manifest=AppManifest(
                    name="Test",
                    description="Test", 
                    version="1.0",
                    author="Test"
                ),
                app_path=Path("/non/existent/path")
            )


class TestSystemManagerIntegration:
    """Integration tests for SystemManager."""
    
    def test_system_manager_initialization(self, event_bus, hardware_manager, app_manager, app_runner):
        """Test SystemManager initialization with all components."""
        # Create system manager using fixtures (mirrors main.py composition)
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_manager,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        # Test that system manager was created with dependencies
        assert system_manager.event_bus == event_bus
        assert system_manager.hardware_service == hardware_manager
        assert system_manager.app_manager == app_manager
        assert system_manager.app_runner == app_runner
    
    def test_system_manager_signal_handling(self, system_manager):
        """Test SystemManager signal handling integration."""
        import signal
        
        # Test signal handler directly (test the handler function rather than actual signals)
        system_manager._running = True
        
        # Call signal handler
        system_manager._signal_handler(signal.SIGTERM, None)
        
        # Verify shutdown was initiated
        assert system_manager._shutdown_event is not None
    
    def test_system_manager_lifecycle(self, event_bus, hardware_manager, app_manager, app_runner):
        """Test SystemManager start/stop lifecycle with lifecycle event assertions."""
        from tests.helpers.runtime import wait_for
        
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_manager,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        # Track lifecycle events
        events_received = []
        def event_handler(event_type, payload):
            events_received.append(event_type)
        
        event_bus.subscribe("system_started", event_handler)
        event_bus.subscribe("system_shutdown", event_handler)
        
        # Start and verify
        system_manager.start()
        assert wait_for(lambda: system_manager._running, timeout=1.0)
        assert wait_for(lambda: "system_started" in events_received, timeout=1.0)
        
        # Stop and verify
        system_manager.stop()
        assert wait_for(lambda: not system_manager._running, timeout=1.0)
        assert wait_for(lambda: "system_shutdown" in events_received, timeout=1.0)


class TestServiceIntegration:
    """Integration tests for service layer components."""
    
    def test_hardware_and_app_manager_integration(self, event_bus, app_manager, hardware_manager):
        """Test integration between hardware events and app management."""
        from tests.helpers.runtime import wait_for
        
        # Simulate hardware switch change that should trigger app lookup
        switch_events = []
        
        def switch_handler(event_type, payload):
            switch_events.append(payload)
            # Simulate looking up app for new switch value
            app = app_manager.get_app_by_switch_value(payload.get("new_value", 0))
            if app:
                # Simulate app found event
                event_bus.publish("app_selected", {
                    "app_name": app.manifest.name,
                    "switch_value": app.switch_value
                }, "test")
        
        event_bus.subscribe("switch_changed", switch_handler)
        
        # Simulate switch change
        event_bus.publish("switch_changed", {"old_value": 0, "new_value": 0}, "test")
        
        # Event-driven wait instead of sleep
        assert wait_for(lambda: len(switch_events) == 1, timeout=0.5)
        assert switch_events[0]["new_value"] == 0
    
    def test_webui_and_system_integration(self, event_bus):
        """Test WebUI integration with system events and lifecycle assertions."""
        from tests.helpers.runtime import wait_for
        
        # Track events that would be relevant to WebUI
        webui_relevant_events = []
        
        def webui_handler(event_type, payload):
            webui_relevant_events.append((event_type, payload))
        
        # Subscribe to lifecycle events that WebUI would care about
        event_bus.subscribe("app_started", webui_handler)
        event_bus.subscribe("app_stopped", webui_handler)
        event_bus.subscribe("hardware_status", webui_handler)
        event_bus.subscribe("system_started", webui_handler)
        
        # Simulate system events that WebUI should respond to
        event_bus.publish("app_started", {"app_name": "Test App", "switch_value": 42}, "test")
        event_bus.publish("hardware_status", {"component": "display", "status": "active", "value": 123}, "test")
        event_bus.publish("system_started", {"hardware_type": "webui"}, "test")
        
        # Event-driven wait for all events
        assert wait_for(lambda: len(webui_relevant_events) == 3, timeout=0.5)
        event_types = [event[0] for event in webui_relevant_events]
        assert "app_started" in event_types
        assert "hardware_status" in event_types
        assert "system_started" in event_types
