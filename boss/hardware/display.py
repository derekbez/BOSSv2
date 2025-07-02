"""
SevenSegmentDisplay: Abstraction for TM1637 7-segment display (or mock for dev)
"""
from typing import Protocol
from gpiozero import Device
import tm1637

class DisplayInterface(Protocol):
    def show_number(self, value: int):
        ...
    def show_message(self, message: str):
        ...


import time

class MockSevenSegmentDisplay:
    """Mock display for development/testing."""
    def __init__(self, event_bus=None):
        self.last_value = None
        self.event_bus = event_bus
    def show_number(self, value: int):
        self.last_value = value
        print(f"[MOCK DISPLAY] 7-segment shows: {value}")
        if self.event_bus:
            self.event_bus.publish(
                "output.display.updated",
                {
                    "value": str(value)[-4:].rjust(4),
                    "timestamp": time.time(),
                    "source": "hardware.display.mock"
                }
            )
    def show_message(self, message: str):
        print(f"[MOCK DISPLAY] 7-segment message: {message}")
        if self.event_bus:
            self.event_bus.publish(
                "output.display.updated",
                {
                    "value": str(message)[:4].rjust(4),
                    "timestamp": time.time(),
                    "source": "hardware.display.mock"
                }
            )


class PiSevenSegmentDisplay:
    """Real TM1637 display using the tm1637_rpi5_gpiod library."""
    def __init__(self, clk_pin, dio_pin, event_bus=None):
        self.display = tm1637.TM1637(clk_pin, dio_pin)
        self.event_bus = event_bus
    def show_number(self, value: int):
        # Show up to 4 digits, pad with spaces if needed
        str_val = str(value)[-4:].rjust(4)
        self.display.show(str_val)
        if self.event_bus:
            self.event_bus.publish(
                "output.display.updated",
                {
                    "value": str_val,
                    "timestamp": time.time(),
                    "source": "hardware.display.pi"
                }
            )
    def show_message(self, message: str):
        # Show up to 4 characters, pad or trim as needed
        try:
            msg = str(message)[:4].rjust(4)
            self.display.show(msg)
            if self.event_bus:
                self.event_bus.publish(
                    "output.display.updated",
                    {
                        "value": msg,
                        "timestamp": time.time(),
                        "source": "hardware.display.pi"
                    }
                )
        except Exception:
            print(f"[7SEG] MESSAGE: {message}")
