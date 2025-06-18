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
