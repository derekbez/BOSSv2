"""
Button abstraction for B.O.S.S. (with mock for dev)
"""
from typing import Protocol, Callable

class ButtonInterface(Protocol):
    def is_pressed(self) -> bool:
        ...
    def set_callback(self, callback: Callable[[], None]):
        ...

class MockButton:
    def __init__(self, name: str):
        self.name = name
        self._pressed = False
        self._callback = None
    def press(self):
        self._pressed = True
        if self._callback:
            self._callback()
    def release(self):
        self._pressed = False
    def is_pressed(self) -> bool:
        return self._pressed
    def set_callback(self, callback: Callable[[], None]):
        self._callback = callback

try:
    from gpiozero import Button as GpiozeroButton
    HAS_GPIOZERO = True
except ImportError:
    HAS_GPIOZERO = False

class PiButton:
    def __init__(self, pin: int, pull_up: bool = True, bounce_time: float = 0.05):
        if not HAS_GPIOZERO:
            raise ImportError("gpiozero is required for PiButton")
        self._button = GpiozeroButton(pin, pull_up=pull_up, bounce_time=bounce_time)
        self._callback = None
    def is_pressed(self) -> bool:
        return self._button.is_pressed
    def set_callback(self, callback: Callable[[], None]):
        self._callback = callback
        self._button.when_pressed = callback
    def close(self):
        self._button.close()
