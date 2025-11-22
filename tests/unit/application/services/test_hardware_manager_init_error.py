from unittest.mock import Mock
import pytest
from boss.core import HardwareManager


def test_hardware_manager_initialize_component_error(monkeypatch):
    factory = Mock()
    event_bus = Mock()
    # Configure factory to raise on create_display (first component)
    factory.create_buttons.return_value = Mock()
    factory.create_go_button.return_value = Mock()
    factory.create_leds.return_value = Mock()
    factory.create_switches.return_value = Mock()
    factory.create_display.side_effect = RuntimeError('display fail')
    factory.create_screen.return_value = Mock()
    factory.create_speaker.return_value = None
    factory.hardware_type = 'mock'

    hm = HardwareManager(factory, event_bus)
    with pytest.raises(RuntimeError):
        hm.initialize()
