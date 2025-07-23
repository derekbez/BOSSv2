"""
Integration tests for domain models and system components.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from boss.domain.models.app import App, AppManifest, AppStatus
from boss.application.services.system_service import SystemManager
from boss.application.events.event_bus import EventBus


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
    
    def test_system_manager_initialization(self, mock_config, mock_hardware_factory):
        """Test SystemManager initialization with all components."""
        event_bus = EventBus()
        event_bus.start()
        
        try:
            from boss.application.services.app_manager import AppManager
            from boss.application.services.app_runner import AppRunner
            from boss.application.services.hardware_service import HardwareManager
            
            # Create mock components
            hardware_service = Mock()
            app_manager = Mock()
            app_runner = Mock()
            
            # Create system manager with dependencies
            system_manager = SystemManager(
                event_bus=event_bus,
                hardware_service=hardware_service,
                app_manager=app_manager,
                app_runner=app_runner
            )
            
            # Test that system manager was created with dependencies
            assert system_manager.event_bus == event_bus
            assert system_manager.hardware_service == hardware_service
            assert system_manager.app_manager == app_manager
            assert system_manager.app_runner == app_runner
            
        finally:
            event_bus.stop()
    
    def test_system_manager_signal_handling(self):
        """Test SystemManager signal handling integration."""
        import signal
        import threading
        
        event_bus = EventBus()
        
        # Create system manager with mock dependencies
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=Mock(),
            app_manager=Mock(),
            app_runner=Mock()
        )
        
        # Test signal handler directly
        # Note: We test the handler function rather than actual signals
        original_running = system_manager._running
        system_manager._running = True
        
        # Call signal handler
        system_manager._signal_handler(signal.SIGTERM, None)
        
        # Verify shutdown was initiated
        # (The actual implementation would call stop())
        assert system_manager._shutdown_event is not None
    
    def test_system_manager_lifecycle(self):
        """Test SystemManager start/stop lifecycle."""
        event_bus = EventBus()
        hardware_service = Mock()
        app_manager = Mock()
        app_runner = Mock()
        
        # Configure hardware service mock
        hardware_service.hardware_factory.hardware_type = "mock"
        
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_service,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        # Test start
        system_manager.start()
        
        # Verify start sequence
        assert system_manager._running == True
        hardware_service.initialize.assert_called_once()
        app_manager.load_apps.assert_called_once()
        hardware_service.start_monitoring.assert_called_once()
        
        # Test stop
        system_manager.stop()
        
        # Verify stop sequence
        assert system_manager._running == False
        app_runner.stop_current_app.assert_called_once()
        hardware_service.stop_monitoring.assert_called_once()
        hardware_service.cleanup.assert_called_once()


class TestServiceIntegration:
    """Integration tests for service layer components."""
    
    def test_hardware_and_app_manager_integration(self, temp_apps_directory, temp_config_directory, mock_hardware_factory):
        """Test integration between hardware events and app management."""
        event_bus = EventBus()
        event_bus.start()
        
        try:
            from boss.application.services.app_manager import AppManager
            from boss.application.services.hardware_service import HardwareManager
            
            # Create managers
            app_manager = AppManager(temp_apps_directory, event_bus)
            app_manager._app_mappings_file = temp_config_directory / "app_mappings.json"
            app_manager.load_apps()
            
            hardware_manager = HardwareManager(mock_hardware_factory, event_bus)
            hardware_manager.initialize()
            
            # Simulate hardware switch change that should trigger app lookup
            switch_events = []
            
            def switch_handler(event_type, payload):
                if event_type == "switch_changed":
                    switch_events.append(payload)
                    # Simulate looking up app for new switch value
                    app = app_manager.get_app_by_switch_value(payload.get("new_value", 0))
                    if app:
                        # Simulate app found event
                        event_bus.publish("app_selected", {
                            "app_name": app.manifest.name,
                            "switch_value": app.switch_value
                        })
            
            event_bus.subscribe("switch_changed", switch_handler)
            
            # Simulate switch change
            event_bus.publish("switch_changed", {"old_value": 0, "new_value": 0})
            
            import time
            time.sleep(0.1)  # Let events process
            
            # Verify integration worked
            assert len(switch_events) == 1
            assert switch_events[0]["new_value"] == 0
            
        finally:
            event_bus.stop()
    
    def test_webui_and_system_integration(self, mock_config):
        """Test WebUI integration with system events."""
        event_bus = EventBus()
        event_bus.start()
        
        try:
            # Test WebUI functionality through the presentation layer
            # Track events that would be relevant to WebUI
            webui_relevant_events = []
            
            def webui_handler(event_type, payload):
                if event_type in ["app_started", "app_stopped", "hardware_status", "system_started"]:
                    webui_relevant_events.append((event_type, payload))
            
            # Subscribe to events that WebUI would care about
            event_bus.subscribe("app_started", webui_handler)
            event_bus.subscribe("app_stopped", webui_handler)
            event_bus.subscribe("hardware_status", webui_handler)
            event_bus.subscribe("system_started", webui_handler)
            
            # Simulate system events that WebUI should respond to
            event_bus.publish("app_started", {
                "app_name": "Test App",
                "switch_value": 42
            })
            
            event_bus.publish("hardware_status", {
                "component": "display",
                "status": "active",
                "value": 123
            })
            
            event_bus.publish("system_started", {
                "hardware_type": "webui"
            })
            
            import time
            time.sleep(0.1)  # Let events process
            
            # Verify WebUI-relevant events were captured
            assert len(webui_relevant_events) == 3
            event_types = [event[0] for event in webui_relevant_events]
            assert "app_started" in event_types
            assert "hardware_status" in event_types
            assert "system_started" in event_types
            
        finally:
            event_bus.stop()
