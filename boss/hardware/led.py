"""
LED abstraction for B.O.S.S. (with mock for dev)
"""
from typing import Protocol

class LEDInterface(Protocol):
    def set_state(self, on: bool):
        ...

class MockLED:
    def __init__(self, color: str):
        self.color = color
        self.state = False
    def set_state(self, on: bool):
        self.state = on
        print(f"[MOCK LED] {self.color} LED is now {'ON' if on else 'OFF'}")
