"""
SwitchReader: Reads value from 8 toggle switches via 74HC151 multiplexer (or mock for dev)
"""
from typing import Protocol

class SwitchInput(Protocol):
    def read_value(self) -> int:
        ...

class MockSwitchReader:
    """Mock switch reader for development/testing."""
    def __init__(self, value: int = 0):
        self._value = value
    def set_value(self, value: int):
        self._value = value
    def read_value(self) -> int:
        return self._value

import sys
import select

class PiSwitchReader:
    """Reads value from 8 toggle switches via 74HC151 multiplexer using gpiozero."""
    def __init__(self, mux_pins, mux_in_pin):
        from gpiozero import OutputDevice, InputDevice
        self.mux_select = [OutputDevice(pin) for pin in mux_pins]
        self.mux_in = InputDevice(mux_in_pin)
    def read_value(self) -> int:
        value = 0
        for i in range(8):
            # Set select lines
            for bit, dev in enumerate(self.mux_select):
                dev.value = (i >> bit) & 1
            # Small delay for signal to settle
            import time; time.sleep(0.001)
            if self.mux_in.value:
                value |= (1 << i)
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
