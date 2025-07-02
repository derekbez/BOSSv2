"""
SwitchReader: Reads value from 8 toggle switches via 74HC151 multiplexer (or mock for dev)
"""
from typing import Protocol

class SwitchInput(Protocol):
    def read_value(self) -> int:
        ...


import time

class MockSwitchReader:
    """Mock switch reader for development/testing."""
    def __init__(self, value: int = 0, event_bus=None):
        self._value = value
        self._prev_value = value
        self.event_bus = event_bus
    def set_value(self, value: int):
        prev = self._value
        self._value = value
        if self.event_bus and prev != value:
            self.event_bus.publish(
                "input.switch.changed",
                {
                    "current_value": value,
                    "previous_value": prev,
                    "timestamp": time.time(),
                    "source": "hardware.switch.mock"
                }
            )
        self._prev_value = prev
    def read_value(self) -> int:
        return self._value

import sys
import select


class PiSwitchReader:
    """Reads value from 8 toggle switches via 74HC151 multiplexer using gpiozero."""
    def __init__(self, mux_pins, mux_in_pin, event_bus=None):
        from gpiozero import OutputDevice, InputDevice
        self.mux_select = [OutputDevice(pin) for pin in mux_pins]
        self.mux_in = InputDevice(mux_in_pin)
        self._last_value = None
        self.event_bus = event_bus
    def read_value(self) -> int:
        value = 0
        for i in range(8):
            # Set select lines
            for bit, dev in enumerate(self.mux_select):
                dev.value = (i >> bit) & 1
            # Small delay for signal to settle
            import time as _t; _t.sleep(0.001)
            if self.mux_in.value:
                value |= (1 << i)
        if self._last_value is not None and value != self._last_value and self.event_bus:
            self.event_bus.publish(
                "input.switch.changed",
                {
                    "current_value": value,
                    "previous_value": self._last_value,
                    "timestamp": time.time(),
                    "source": "hardware.switch.pi"
                }
            )
        self._last_value = value
        return value

class KeyboardSwitchReader:
    """Mock switch reader: user types a number (0-255) in the terminal and blocks until input."""
    def __init__(self, initial=0):
        self._value = initial
    def read_value(self) -> int:
        while True:
            try:
                line = input("Enter switch value (0-255) or press Enter to keep current: ").strip()
                if not line:
                    break
                if line.isdigit():
                    self._value = max(0, min(255, int(line)))
                    break
            except (EOFError, KeyboardInterrupt):
                break
        return self._value

class KeyboardGoButton:
    """Mock Go button: user presses Enter to simulate button press (blocks until Enter)."""
    def __init__(self):
        pass  # Remove any _pressed or is_pressed attribute
    def is_pressed(self):
        input("Press Enter to simulate Go button...")
        return True
