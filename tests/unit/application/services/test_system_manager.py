"""
Unit tests for SystemManager service.
"""

import pytest
import signal
import threading
from unittest.mock import Mock, patch, MagicMock

from boss.application.services.system_service import SystemManager
from boss.application.events.event_bus import EventBus


class TestSystemManager:
    """Unit tests for SystemManager."""
    
    def test_init(self):
        """Test SystemManager initialization."""
        event_bus = Mock()
        hardware_service = Mock()
        app_manager = Mock()
        app_runner = Mock()
        
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_service,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        assert system_manager.event_bus == event_bus
        assert system_manager.hardware_service == hardware_service
        assert system_manager.app_manager == app_manager
        assert system_manager.app_runner == app_runner
        assert system_manager._running == False
        assert isinstance(system_manager._shutdown_event, threading.Event)
    
    def test_start_system(self):
        """Test starting the system."""
        event_bus = Mock()
        hardware_service = Mock()
        app_manager = Mock()
        app_runner = Mock()
        
        # Configure hardware type
        hardware_service.hardware_factory.hardware_type = "mock"
        
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_service,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        with patch.object(system_manager, '_run_startup_app') as mock_startup_app:
            system_manager.start()
        
        # Verify startup sequence
        event_bus.start.assert_called_once()
        hardware_service.initialize.assert_called_once()
        app_manager.load_apps.assert_called_once()
        hardware_service.start_monitoring.assert_called_once()
        mock_startup_app.assert_called_once()
        
        assert system_manager._running == True
        
        # Verify system started event was published
        event_bus.publish.assert_called_with("system_started", {"hardware_type": "mock"}, "system")
    
    def test_start_system_already_running(self):
        """Test starting system when already running."""
        event_bus = Mock()
        hardware_service = Mock()
        app_manager = Mock()
        app_runner = Mock()
        
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_service,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        # Mark as already running
        system_manager._running = True
        
        with patch('boss.application.services.system_service.logger') as mock_logger:
            system_manager.start()
        
        # Should log warning and not start components
        mock_logger.warning.assert_called_with("System already running")
        event_bus.start.assert_not_called()
        hardware_service.initialize.assert_not_called()
    
    def test_start_system_with_error(self):
        """Test starting system when an error occurs."""
        event_bus = Mock()
        hardware_service = Mock()
        app_manager = Mock()
        app_runner = Mock()
        
        # Make hardware initialization fail
        hardware_service.initialize.side_effect = Exception("Hardware error")
        
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_service,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        with patch.object(system_manager, 'stop') as mock_stop:
            with pytest.raises(Exception, match="Hardware error"):
                system_manager.start()
        
        # Should call stop on error
        mock_stop.assert_called_once()
    
    def test_stop_system(self):
        """Test stopping the system."""
        event_bus = Mock()
        hardware_service = Mock()
        app_manager = Mock()
        app_runner = Mock()
        
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_service,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        # Mark as running
        system_manager._running = True
        
        with patch.object(system_manager, 'stop_webui_if_running') as mock_stop_webui:
            system_manager.stop()
        
        # Verify shutdown sequence
        event_bus.publish.assert_called_with("system_shutdown", {"reason": "normal"}, "system")
        mock_stop_webui.assert_called_once()
        app_runner.stop_current_app.assert_called_once()
        hardware_service.stop_monitoring.assert_called_once()
        hardware_service.cleanup.assert_called_once()
        event_bus.stop.assert_called_once()
        
        assert system_manager._running == False
        assert system_manager._shutdown_event.is_set()
    
    def test_stop_system_not_running(self):
        """Test stopping system when not running."""
        event_bus = Mock()
        hardware_service = Mock()
        app_manager = Mock()
        app_runner = Mock()
        
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_service,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        # Not running
        assert system_manager._running == False
        
        system_manager.stop()
        
        # Should not call any shutdown methods
        event_bus.publish.assert_not_called()
        app_runner.stop_current_app.assert_not_called()
    
    def test_signal_handler(self):
        """Test signal handler."""
        event_bus = Mock()
        hardware_service = Mock()
        app_manager = Mock()
        app_runner = Mock()
        
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_service,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        with patch.object(system_manager, 'stop') as mock_stop:
            system_manager._signal_handler(signal.SIGTERM, None)
        
        mock_stop.assert_called_once()
    
    def test_signal_handler_force_exit(self):
        """Test signal handler with force exit."""
        event_bus = Mock()
        hardware_service = Mock()
        app_manager = Mock()
        app_runner = Mock()
        
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_service,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        # Simulate shutdown already in progress
        system_manager._shutdown_event.set()
        
        with patch('boss.application.services.system_service.sys.exit') as mock_exit:
            with patch('boss.application.services.system_service.logger') as mock_logger:
                system_manager._signal_handler(signal.SIGINT, None)
        
        mock_logger.warning.assert_called_with("Force exit: Ctrl+C pressed during shutdown")
        mock_exit.assert_called_with(1)
    
    def test_start_webui_if_needed_webui_type(self):
        """Test starting WebUI for webui hardware type."""
        event_bus = Mock()
        hardware_service = Mock()
        app_manager = Mock()
        app_runner = Mock()
        
        # Mock the hardware components
        hardware_service.buttons = Mock()
        hardware_service.go_button = Mock()
        hardware_service.leds = Mock()
        hardware_service.switches = Mock()
        hardware_service.display = Mock()
        hardware_service.screen = Mock()
        
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_service,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        with patch('boss.application.services.system_service.start_web_ui') as mock_start_webui:
            mock_start_webui.return_value = 8080
            
            system_manager.start_webui_if_needed("webui")
        
        assert system_manager._webui_port == 8080
        mock_start_webui.assert_called_once()
    
    def test_start_webui_if_needed_other_type(self):
        """Test not starting WebUI for non-webui hardware type."""
        event_bus = Mock()
        hardware_service = Mock()
        app_manager = Mock()
        app_runner = Mock()
        
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_service,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        with patch('boss.application.services.system_service.start_web_ui') as mock_start_webui:
            system_manager.start_webui_if_needed("raspberry_pi")
        
        # Should not start WebUI
        mock_start_webui.assert_not_called()
        assert system_manager._webui_port is None
    
    def test_stop_webui_if_running(self):
        """Test stopping WebUI when running."""
        event_bus = Mock()
        hardware_service = Mock()
        app_manager = Mock()
        app_runner = Mock()
        
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_service,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        # Set WebUI as running
        system_manager._webui_port = 8080
        
        with patch('boss.application.services.system_service.stop_web_ui') as mock_stop_webui:
            system_manager.stop_webui_if_running()
        
        mock_stop_webui.assert_called_once()
        assert system_manager._webui_port is None
    
    def test_stop_webui_if_running_not_running(self):
        """Test stopping WebUI when not running."""
        event_bus = Mock()
        hardware_service = Mock()
        app_manager = Mock()
        app_runner = Mock()
        
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_service,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        # WebUI not running
        assert system_manager._webui_port is None
        
        with patch('boss.application.services.system_service.stop_web_ui') as mock_stop_webui:
            system_manager.stop_webui_if_running()
        
        # Should not call stop
        mock_stop_webui.assert_not_called()
    
    def test_setup_event_handlers(self):
        """Test event handler setup."""
        event_bus = Mock()
        hardware_service = Mock()
        app_manager = Mock()
        app_runner = Mock()
        
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_service,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        # Verify event subscriptions were set up
        expected_subscriptions = [
            ("app_launch_requested", system_manager._on_app_launch_requested),
            ("go_button_pressed", system_manager._on_go_button_pressed),
            ("system_shutdown", system_manager._on_system_shutdown_requested),
            ("led_update", system_manager._on_led_update),
            ("display_update", system_manager._on_display_update),
            ("screen_update", system_manager._on_screen_update)
        ]
        
        # Check that subscribe was called for each expected event
        assert event_bus.subscribe.call_count == len(expected_subscriptions)
        
    def test_on_app_launch_requested(self):
        """Test app launch request handler."""
        event_bus = Mock()
        hardware_service = Mock()
        app_manager = Mock()
        app_runner = Mock()
        
        # Mock hardware state
        mock_hardware_state = Mock()
        mock_hardware_state.switches.value = 5
        hardware_service.get_hardware_state.return_value = mock_hardware_state
        
        # Mock app for switch value
        mock_app = Mock()
        mock_app.manifest.name = "Test App"
        app_manager.get_app_by_switch_value.return_value = mock_app
        
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_service,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        payload = {}
        system_manager._on_app_launch_requested("app_launch_requested", payload)
        
        # Should get hardware state, find app, and start it
        hardware_service.get_hardware_state.assert_called_once()
        app_manager.get_app_by_switch_value.assert_called_with(5)
        app_runner.start_app.assert_called_with(mock_app)
        app_manager.set_current_app.assert_called_with(mock_app)
    
    def test_on_go_button_pressed(self):
        """Test go button press handler."""
        event_bus = Mock()
        hardware_service = Mock()
        app_manager = Mock()
        app_runner = Mock()
        
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_service,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        payload = {}
        system_manager._on_go_button_pressed("go_button_pressed", payload)
        
        # Should publish app launch request
        event_bus.publish.assert_called_with("app_launch_requested", {}, "system")
    
    def test_on_led_update(self):
        """Test LED update handler."""
        event_bus = Mock()
        hardware_service = Mock()
        app_manager = Mock()
        app_runner = Mock()
        
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_service,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        payload = {"color": "red", "is_on": True, "brightness": 0.8}
        system_manager._on_led_update("led_update", payload)
        
        # Should call hardware service
        hardware_service.update_led.assert_called_with("red", True, 0.8)
    
    def test_on_display_update(self):
        """Test display update handler."""
        event_bus = Mock()
        hardware_service = Mock()
        app_manager = Mock()
        app_runner = Mock()
        
        system_manager = SystemManager(
            event_bus=event_bus,
            hardware_service=hardware_service,
            app_manager=app_manager,
            app_runner=app_runner
        )
        
        payload = {"value": 123, "brightness": 0.9}
        system_manager._on_display_update("display_update", payload)
        
        # Should call hardware service
        hardware_service.update_display.assert_called_with(123, 0.9)
