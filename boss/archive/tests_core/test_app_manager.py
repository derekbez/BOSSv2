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

def test_display_no_update_on_same_value():
    switch = MockSwitchReader(5)
    display = MockSevenSegmentDisplay()
    manager = AppManager(switch, display)
    manager.run_once()
    display.last_value = 123  # Simulate display changed elsewhere
    manager.run_once()
    # Should not overwrite display if value hasn't changed
    assert display.last_value == 123

def test_display_edge_cases():
    switch = MockSwitchReader(-1)
    display = MockSevenSegmentDisplay()
    manager = AppManager(switch, display)
    manager.run_once()
    assert display.last_value == -1
    switch.set_value(255)
    manager.run_once()
    assert display.last_value == 255
