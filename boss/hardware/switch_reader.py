"""
SwitchReader: Reads value from 8 toggle switches via 74HC151 multiplexer (or mock for dev)
"""
from typing import Protocol

class SwitchInput(Protocol):
    def read_value(self) -> int:
        ...


import time

SWITCH_CHANGED_EVENT = "input.switch.changed"

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
                SWITCH_CHANGED_EVENT,
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

    def close(self):
        pass  # No resources to release in mock

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
                SWITCH_CHANGED_EVENT,
                {
                    "current_value": value,
                    "previous_value": self._last_value,
                    "timestamp": time.time(),
                    "source": "hardware.switch.pi"
                }
            )
        self._last_value = value
        return value

class APISwitchReader:
    """Mock switch reader for dev/web UI: value is set via API/web UI, not keyboard. Only KeyboardInterrupt/EOFError exits."""
    def __init__(self, initial=0, event_bus=None):
        self._value = initial
        self.event_bus = event_bus
        self._prev_value = initial
    def read_value(self) -> int:
        # In web UI/dev mode, just return the current value (no keyboard input)
        return self._value
    def set_value(self, value: int):
        prev = self._value
        self._value = value
        # Always publish a switch_change event for web UI compatibility
        if self.event_bus:
            self.event_bus.publish(
                "switch_change",
                {
                    "value": value,
                    "previous_value": prev,
                    "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                }
            )
        self._prev_value = prev
    def close(self):
        pass  # No resources to release in mock
