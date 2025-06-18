import pytest
from boss.core.app_manager import AppManager
from boss.hardware.switch_reader import MockSwitchReader
from boss.hardware.display import MockSevenSegmentDisplay

def test_display_updates_on_switch_change():
    switch = MockSwitchReader(0)
    display = MockSevenSegmentDisplay()
    manager = AppManager(switch, display)

    # Initial poll, should update display
    assert manager.run_once() == 0
    assert display.last_value == 0

    # Change switch value
    switch.set_value(42)
    assert manager.run_once() == 42
    assert display.last_value == 42

    # No change, display should not update again
    assert manager.run_once() == 42
    assert display.last_value == 42
