"""
LED abstraction for B.O.S.S. (with mock for dev)
"""
from typing import Protocol

class LEDInterface(Protocol):
    def set_state(self, on: bool):
        ...


import time

class MockLED:
    def __init__(self, color: str, event_bus=None):
        self.color = color
        self._state = False
        self.event_bus = event_bus
    def set_state(self, on: bool):
        self._state = on
        print(f"[MOCK LED] {self.color} LED is now {'ON' if on else 'OFF'}")
        if self.event_bus:
            self.event_bus.publish(
                "output.led.state_changed",
                {
                    "led_id": self.color,
                    "state": "on" if on else "off",
                    "timestamp": time.time(),
                    "source": f"hardware.led.{self.color}"
                }
            )

    def on(self):
        self.set_state(True)

    def off(self):
        self.set_state(False)

    def is_on(self):
        return self._state

    def close(self):
        pass  # No resources to release in mock

try:
    from gpiozero import LED as GpiozeroLED
    HAS_GPIOZERO = True
except ImportError:
    HAS_GPIOZERO = False


class PiLED:
    def __init__(self, pin: int, color: str = None, event_bus=None):
        if not HAS_GPIOZERO:
            raise ImportError("gpiozero is required for PiLED")
        self._led = GpiozeroLED(pin)
        self.color = color or str(pin)
        self.event_bus = event_bus
    def set_state(self, on: bool):
        if on:
            self._led.on()
        else:
            self._led.off()
        if self.event_bus:
            self.event_bus.publish(
                "output.led.state_changed",
                {
                    "led_id": self.color,
                    "state": "on" if on else "off",
                    "timestamp": time.time(),
                    "source": f"hardware.led.{self.color}"
                }
            )
    def on(self):
        self.set_state(True)
    def off(self):
        self.set_state(False)
    def close(self):
        self._led.close()
