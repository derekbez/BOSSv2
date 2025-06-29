"""
SevenSegmentDisplay: Abstraction for TM1637 7-segment display (or mock for dev)
"""
from typing import Protocol
from gpiozero import Device
from rpi_tm1637 import TM1637

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

class PiSevenSegmentDisplay:
    """Real TM1637 display using the rpi_tm1637 library."""
    def __init__(self, clk_pin, dio_pin):
        self.display = TM1637(clk=clk_pin, dio=dio_pin)
    def show_number(self, value: int):
        # Show up to 4 digits, pad with spaces if needed
        str_val = str(value)[-4:].rjust(4)
        self.display.show(str_val)
    def show_message(self, message: str):
        # For compatibility with MockSevenSegmentDisplay
        # If message is numeric, display as number; else, show as scrolling text or fallback
        try:
            num = int(message)
            self.show_number(num)
        except Exception:
            # No scrolling text support; just print to console for now
            print(f"[7SEG] MESSAGE: {message}")
