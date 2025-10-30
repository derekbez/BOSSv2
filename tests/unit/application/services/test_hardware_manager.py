"""
Unit tests for HardwareManager service.
"""

from unittest.mock import Mock, patch

from boss.core import HardwareManager


class TestHardwareManager:
    def test_init(self, mock_hardware_factory):
        event_bus = Mock()
        hm = HardwareManager(mock_hardware_factory, event_bus)
        assert hm.hardware_factory == mock_hardware_factory
        assert hm.event_bus == event_bus
        assert hm.buttons is None
        assert hm.go_button is None
        assert hm.leds is None
        assert hm.switches is None
        assert hm.display is None
        assert hm.screen is None
        assert hm.speaker is None
        assert hm._monitoring_thread is None
        assert hm._monitoring_active is False
        assert hm._last_switch_value == 0

    def test_initialize(self, mock_hardware_factory):
        event_bus = Mock()
    # components from fixture already return objects whose initialize() returns True
        hm = HardwareManager(mock_hardware_factory, event_bus)
        with patch.object(hm, '_setup_callbacks'), \
             patch.object(hm, '_setup_webui_event_bus'), \
             patch.object(hm, '_update_hardware_state'):
            hm.initialize()

        assert hm.buttons is not None
        assert hm.go_button is not None
        assert hm.leds is not None
        assert hm.switches is not None
        assert hm.display is not None
        assert hm.screen is not None
        assert hm.speaker is not None

        mock_hardware_factory.create_buttons.assert_called_once()
        mock_hardware_factory.create_go_button.assert_called_once()
        mock_hardware_factory.create_leds.assert_called_once()
        mock_hardware_factory.create_switches.assert_called_once()
        mock_hardware_factory.create_display.assert_called_once()
        mock_hardware_factory.create_screen.assert_called_once()
        mock_hardware_factory.create_speaker.assert_called_once()

    def test_cleanup(self, mock_hardware_factory):
        event_bus = Mock()
        hm = HardwareManager(mock_hardware_factory, event_bus)
        # assign mocks
        hm.buttons = Mock()
        hm.go_button = Mock()
        hm.leds = Mock()
        hm.switches = Mock()
        hm.display = Mock()
        hm.screen = Mock()
        hm.speaker = Mock()
        with patch.object(hm, 'stop_monitoring'):
            hm.cleanup()
        hm.buttons.cleanup.assert_called_once()
        hm.go_button.cleanup.assert_called_once()
        hm.leds.cleanup.assert_called_once()
        hm.switches.cleanup.assert_called_once()
        hm.display.cleanup.assert_called_once()
        hm.screen.cleanup.assert_called_once()
        hm.speaker.cleanup.assert_called_once()

    def test_start_stop_monitoring(self, mock_hardware_factory):
        event_bus = Mock()
        hm = HardwareManager(mock_hardware_factory, event_bus)
        with patch.object(hm, '_monitor_hardware'):
            hm.start_monitoring()
        assert hm._monitoring_active is True
        assert hm._monitoring_thread is not None
    # Thread target is patched; thread may terminate immediately. Just ensure a Thread object was created.
        hm.stop_monitoring()
        assert hm._monitoring_active is False

    def test_get_hardware_state(self, mock_hardware_factory):
        event_bus = Mock()
        hm = HardwareManager(mock_hardware_factory, event_bus)
        with patch.object(hm, '_update_hardware_state'):
            state = hm.get_hardware_state()
        assert state is not None
        assert state == hm._hardware_state

    def test_update_led(self, mock_hardware_factory):
        event_bus = Mock()
        hm = HardwareManager(mock_hardware_factory, event_bus)
        hm.leds = Mock()
        hm.update_led("red", True, 0.8)
        hm.leds.set_led.assert_called_once()

    def test_update_display(self, mock_hardware_factory):
        event_bus = Mock()
        hm = HardwareManager(mock_hardware_factory, event_bus)
        hm.display = Mock()
        hm.update_display(123, 0.9)
        # Accept positional or keyword brightness
        assert hm.display.show_number.called
        hm.update_display(None, 1.0)
        hm.display.clear.assert_called_with()

    def test_update_screen(self, mock_hardware_factory):
        event_bus = Mock()
        hm = HardwareManager(mock_hardware_factory, event_bus)
        hm.screen = Mock()
        hm.update_screen("text", "Hello World", color="white")
        hm.screen.display_text.assert_called_with("Hello World", color="white")
        hm.update_screen("image", "/path/to/image.png", scale=2.0)
        hm.screen.display_image.assert_called_with("/path/to/image.png", scale=2.0)
        hm.update_screen("clear", "", color="black")
        hm.screen.clear_screen.assert_called_with("black")
