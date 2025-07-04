"""
SevenSegmentDisplay: Abstraction for TM1637 7-segment display (or mock for dev)
"""
from typing import Protocol

# --- Hardware import fallback logic ---
import sys
IS_RPI = sys.platform.startswith('linux') and not sys.platform.startswith('win')
try:
    if IS_RPI:
        from gpiozero import Device
        import tm1637
    else:
        raise ImportError
except ImportError:
    Device = None
    tm1637 = None

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
        self.last_value = message
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

    def close(self):
        pass  # No resources to release in mock



class PiSevenSegmentDisplay:
    """Real TM1637 display using the tm1637 library (only on RPi)."""
    def __init__(self, clk_pin, dio_pin, event_bus=None):
        if tm1637 is None:
            raise RuntimeError("tm1637 library not available; cannot use PiSevenSegmentDisplay on this platform.")
        self.display = tm1637.TM1637(clk_pin, dio_pin)
        self.event_bus = event_bus
    def show_number(self, value: int):
        str_val = str(value)[-4:].rjust(4)
        try:
            self.display.show(str_val)
        except Exception as e:
            print(f"[7SEG ERROR] show_number: {e}")
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
        try:
            msg = str(message)[:4].rjust(4)
            self.display.show(msg)
        except Exception as e:
            print(f"[7SEG ERROR] show_message: {e}")
        if self.event_bus:
            self.event_bus.publish(
                "output.display.updated",
                {
                    "value": msg if 'msg' in locals() else str(message),
                    "timestamp": time.time(),
                    "source": "hardware.display.pi"
                }
            )
