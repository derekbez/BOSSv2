"""
Button abstraction for B.O.S.S. (with mock for dev)
"""
from typing import Protocol, Callable
import time
import threading

class ButtonInterface(Protocol):
    def is_pressed(self) -> bool:
        ...
    def set_callback(self, callback: Callable[[], None]):
        ...
    def close(self):
        ...


class APIButton:
    """Mock button for web UI/dev mode: can be pressed via API/web UI, not keyboard."""
    def __init__(self, name: str, event_bus=None, button_id=None):
        self.name = name
        self._pressed = False
        self._callback = None
        self.event_bus = event_bus
        self.button_id = button_id or name

    def press(self):
        self._pressed = True
        if self.event_bus:
            self.event_bus.publish(
                "input.button.pressed",
                {
                    "button_id": self.button_id,
                    "timestamp": time.time(),
                    "source": f"hardware.button.api.{self.button_id}"
                }
            )
        if self._callback:
            self._callback()
        
        # Automatically release after a short delay to simulate a real button press
        def auto_release():
            time.sleep(0.05) # 50ms delay
            self.release()
        
        threading.Thread(target=auto_release, daemon=True).start()

    def release(self):
        self._pressed = False
        if self.event_bus:
            self.event_bus.publish(
                "input.button.released",
                {
                    "button_id": self.button_id,
                    "timestamp": time.time(),
                    "source": f"hardware.button.api.{self.button_id}"
                }
            )

    def is_pressed(self) -> bool:
        return self._pressed

    def set_callback(self, callback: Callable[[], None]):
        self._callback = callback

    def on(self):
        self.press()

    def off(self):
        self.release()

    def close(self):
        pass

# Legacy alias for APIButton for compatibility.
MockButton = APIButton

try:
    from gpiozero import Button as GpiozeroButton
    HAS_GPIOZERO = True
except ImportError:
    HAS_GPIOZERO = False

class PiButton:
    def __init__(self, pin: int, pull_up: bool = True, bounce_time: float = 0.05, event_bus=None, button_id=None):
        if not HAS_GPIOZERO:
            raise ImportError("gpiozero is required for PiButton")
        self._button = GpiozeroButton(pin, pull_up=pull_up, bounce_time=bounce_time)
        self._callback = None
        self.event_bus = event_bus
        self.button_id = button_id or str(pin)
        self._button.when_pressed = self._handle_press
        self._button.when_released = self._handle_release

    def _handle_press(self):
        if self.event_bus:
            self.event_bus.publish(
                "input.button.pressed",
                {
                    "button_id": self.button_id,
                    "timestamp": time.time(),
                    "source": f"hardware.button.{self.button_id}"
                }
            )
        if self._callback:
            self._callback()

    def _handle_release(self):
        if self.event_bus:
            self.event_bus.publish(
                "input.button.released",
                {
                    "button_id": self.button_id,
                    "timestamp": time.time(),
                    "source": f"hardware.button.{self.button_id}"
                }
            )

    def is_pressed(self) -> bool:
        return self._button.is_pressed

    def set_callback(self, callback: Callable[[], None]):
        self._callback = callback

    def close(self):
        self._button.close()
