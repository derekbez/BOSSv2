"""
Unit tests for HardwareManager service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from boss.application.services.hardware_service import HardwareManager
from boss.application.events.event_bus import EventBus


class TestHardwareManager:
    """Unit tests for HardwareManager."""
    
    def test_init(self, mock_hardware_factory):
        """Test HardwareManager initialization."""
        event_bus = Mock()
        
        hardware_manager = HardwareManager(mock_hardware_factory, event_bus)
        
        assert hardware_manager.hardware_factory == mock_hardware_factory
        assert hardware_manager.event_bus == event_bus
        assert hardware_manager.buttons is None
        assert hardware_manager.go_button is None
        assert hardware_manager.leds is None
        assert hardware_manager.switches is None
        assert hardware_manager.display is None
        assert hardware_manager.screen is None
        assert hardware_manager.speaker is None
        assert hardware_manager._monitoring_thread is None
        assert hardware_manager._monitoring_active == False
        assert hardware_manager._last_switch_value == 0
    
    def test_initialize(self, mock_hardware_factory):
        """Test hardware initialization."""
        event_bus = Mock()
        
        # Mock component initialization success
        for component in [mock_hardware_factory.create_buttons(),
                         mock_hardware_factory.create_go_button(),
                         mock_hardware_factory.create_leds(),
                         mock_hardware_factory.create_switches(),
                         mock_hardware_factory.create_display(),
                         mock_hardware_factory.create_screen(),
                         mock_hardware_factory.create_speaker()]:
            component.initialize.return_value = True
        
        hardware_manager = HardwareManager(mock_hardware_factory, event_bus)
        
        with patch.object(hardware_manager, '_setup_callbacks'), \
             patch.object(hardware_manager, '_setup_webui_event_bus'), \
             patch.object(hardware_manager, '_setup_event_subscriptions'), \
             patch.object(hardware_manager, '_update_hardware_state'):
            
            hardware_manager.initialize()
        
        # Verify all hardware components were created
        assert hardware_manager.buttons is not None
        assert hardware_manager.go_button is not None
        assert hardware_manager.leds is not None
        assert hardware_manager.switches is not None
        assert hardware_manager.display is not None
        assert hardware_manager.screen is not None
        assert hardware_manager.speaker is not None
        
        # Verify hardware factory methods were called
        mock_hardware_factory.create_buttons.assert_called_once()
        mock_hardware_factory.create_go_button.assert_called_once()
        mock_hardware_factory.create_leds.assert_called_once()
        mock_hardware_factory.create_switches.assert_called_once()
        mock_hardware_factory.create_display.assert_called_once()
        mock_hardware_factory.create_screen.assert_called_once()
        mock_hardware_factory.create_speaker.assert_called_once()
    
    def test_cleanup(self, mock_hardware_factory):
        """Test hardware cleanup."""
        event_bus = Mock()
        
        hardware_manager = HardwareManager(mock_hardware_factory, event_bus)
        
        # Create mock components
        mock_buttons = Mock()
        mock_go_button = Mock()
        mock_leds = Mock()
        mock_switches = Mock()
        mock_display = Mock()
        mock_screen = Mock()
        mock_speaker = Mock()
        
        # Assign mock components
        hardware_manager.buttons = mock_buttons
        hardware_manager.go_button = mock_go_button
        hardware_manager.leds = mock_leds
        hardware_manager.switches = mock_switches
        hardware_manager.display = mock_display
        hardware_manager.screen = mock_screen
        hardware_manager.speaker = mock_speaker
        
        with patch.object(hardware_manager, 'stop_monitoring'):
            hardware_manager.cleanup()
        
        # Verify cleanup was called on all components
        mock_buttons.cleanup.assert_called_once()
        mock_go_button.cleanup.assert_called_once()
        mock_leds.cleanup.assert_called_once()
        mock_switches.cleanup.assert_called_once()
        mock_display.cleanup.assert_called_once()
        mock_screen.cleanup.assert_called_once()
        mock_speaker.cleanup.assert_called_once()
    
    def test_start_monitoring(self, mock_hardware_factory):
        """Test starting hardware monitoring."""
        event_bus = Mock()
        
        hardware_manager = HardwareManager(mock_hardware_factory, event_bus)
        
        with patch.object(hardware_manager, '_monitor_hardware'):
            hardware_manager.start_monitoring()
        
        # Verify monitoring was started
        assert hardware_manager._monitoring_active == True
        assert hardware_manager._monitoring_thread is not None
        assert hardware_manager._monitoring_thread.is_alive()
    
    def test_stop_monitoring(self, mock_hardware_factory):
        """Test stopping hardware monitoring."""
        event_bus = Mock()
        
        hardware_manager = HardwareManager(mock_hardware_factory, event_bus)
        
        # Start monitoring first
        hardware_manager.start_monitoring()
        assert hardware_manager._monitoring_active == True
        
        # Stop monitoring
        hardware_manager.stop_monitoring()
        
        # Verify monitoring was stopped
        assert hardware_manager._monitoring_active == False
    
    def test_get_hardware_state(self, mock_hardware_factory):
        """Test getting hardware state."""
        event_bus = Mock()
        
        hardware_manager = HardwareManager(mock_hardware_factory, event_bus)
        
        with patch.object(hardware_manager, '_update_hardware_state'):
            state = hardware_manager.get_hardware_state()
        
        # Verify state was retrieved
        assert state is not None
        assert state == hardware_manager._hardware_state
    
    def test_update_led(self, mock_hardware_factory):
        """Test LED update."""
        event_bus = Mock()
        
        hardware_manager = HardwareManager(mock_hardware_factory, event_bus)
        
        # Create mock LED component
        mock_leds = Mock()
        hardware_manager.leds = mock_leds
        
        # Test LED update
        hardware_manager.update_led("red", True, 0.8)
        
        # Should call LED component
        mock_leds.set_led.assert_called_once()
    
    def test_update_display(self, mock_hardware_factory):
        """Test display update."""
        event_bus = Mock()
        
        hardware_manager = HardwareManager(mock_hardware_factory, event_bus)
        
        # Create mock display component
        mock_display = Mock()
        hardware_manager.display = mock_display
        
        # Test display update with number
        hardware_manager.update_display(123, 0.9)
        
        mock_display.show_number.assert_called_with(123, brightness=0.9)
        
        # Test display update with None
        hardware_manager.update_display(None, 1.0)
        
        mock_display.show_number.assert_called_with(None, brightness=1.0)
    
    def test_update_screen(self, mock_hardware_factory):
        """Test screen update."""
        event_bus = Mock()
        
        hardware_manager = HardwareManager(mock_hardware_factory, event_bus)
        
        # Create mock screen component
        mock_screen = Mock()
        hardware_manager.screen = mock_screen
        
        # Test text update
        hardware_manager.update_screen("text", "Hello World", color="white")
        
        mock_screen.show_text.assert_called_with("Hello World", color="white")
        
        # Test image update
        hardware_manager.update_screen("image", "/path/to/image.png", scale=2.0)
        
        mock_screen.show_image.assert_called_with("/path/to/image.png", scale=2.0)
        
        # Test clear
        hardware_manager.update_screen("clear", "", color="black")
        
        mock_screen.clear.assert_called_with(color="black")
