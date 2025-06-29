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

try:
    from gpiozero import LED as GpiozeroLED
    HAS_GPIOZERO = True
except ImportError:
    HAS_GPIOZERO = False

class PiLED:
    def __init__(self, pin: int):
        if not HAS_GPIOZERO:
            raise ImportError("gpiozero is required for PiLED")
        self._led = GpiozeroLED(pin)
    def set_state(self, on: bool):
        if on:
            self._led.on()
        else:
            self._led.off()
    def on(self):
        self._led.on()
    def off(self):
        self._led.off()
    def close(self):
        self._led.close()
