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

# Real implementation would use gpiozero/pigpio and actual GPIO pins
# class PiSwitchReader:
#     ...
