"""
SevenSegmentDisplay: Abstraction for TM1637 7-segment display (or mock for dev)
"""
from typing import Protocol
from gpiozero import Device
import tm1637 # tm1637_rpi5_gpiod

class DisplayInterface(Protocol):
    def show_number(self, value: int):
        ...
    def show_message(self, message: str):
        ...

class MockSevenSegmentDisplay:
    """Mock display for development/testing."""
    def __init__(self):
        self.last_value = None
    def show_number(self, value: int):
        self.last_value = value
        print(f"[MOCK DISPLAY] 7-segment shows: {value}")
    def show_message(self, message: str):
        print(f"[MOCK DISPLAY] 7-segment message: {message}")

class PiSevenSegmentDisplay:
    """Real TM1637 display using the tm1637_rpi5_gpiod library."""
    def __init__(self, clk_pin, dio_pin):
        self.display = tm1637.TM1637(clk=clk_pin, dio=dio_pin)
    def show_number(self, value: int):
        # Show up to 4 digits, pad with spaces if needed
        str_val = str(value)[-4:].rjust(4)
        self.display.show(str_val)
    def show_message(self, message: str):
        # Show up to 4 characters, pad or trim as needed
        try:
            msg = str(message)[:4].rjust(4)
            self.display.show(msg)
        except Exception:
            print(f"[7SEG] MESSAGE: {message}")
