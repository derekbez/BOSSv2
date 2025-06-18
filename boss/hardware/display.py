"""
SevenSegmentDisplay: Abstraction for TM1637 7-segment display (or mock for dev)
"""
from typing import Protocol

class DisplayInterface(Protocol):
    def show_number(self, value: int):
        ...

class MockSevenSegmentDisplay:
    """Mock display for development/testing."""
    def __init__(self):
        self.last_value = None
    def show_number(self, value: int):
        self.last_value = value
        print(f"[MOCK DISPLAY] 7-segment shows: {value}")

# Real implementation would use rpi-tm1637 or similar
# class PiSevenSegmentDisplay:
#     ...
