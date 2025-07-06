"""
AppAPI: Unified interface for mini-apps to access hardware and system features in B.O.S.S.
"""
from typing import Dict, Any, List, Optional
import time

class AppAPI:
    # Font size constants for all screens (real or mock)
    FONT_SIZE_LARGEST = 64
    FONT_SIZE_LARGER = 48
    FONT_SIZE_DEFAULT = 32
    FONT_SIZE_SMALLER = 24
    FONT_SIZE_SMALLEST = 16

    def __init__(self, screen, buttons: Dict[str, Any], leds: Dict[str, Any], event_bus=None, logger=None):
        self.screen = screen
        self.buttons = buttons  # dict: color -> button instance
        self.leds = leds        # dict: color -> led instance
        self.event_bus = event_bus
        self.logger = logger

    def wait_for_button(self, button_colors: List[str], timeout: float = 0.2) -> Optional[str]:
        """
        Wait for one of the specified buttons to be pressed within the timeout.
        While waiting, illuminate the corresponding LEDs.
        Returns the color of the button pressed, or None if timeout.
        """
        # Light up only the active buttons' LEDs
        self.set_leds({color: (color in button_colors) for color in self.leds})
        start = time.time()
        while time.time() - start < timeout:
            for color in button_colors:
                btn = self.buttons.get(color)
                if btn and callable(getattr(btn, 'is_pressed', None)) and btn.is_pressed():
                    return color
            time.sleep(0.01)
        return None

    def set_led(self, color: str, state: bool):
        led = self.leds.get(color)
        if led:
            try:
                if state:
                    if callable(getattr(led, 'on', None)):
                        led.on()
                else:
                    if callable(getattr(led, 'off', None)):
                        led.off()
            except Exception:
                pass

    def set_leds(self, states: Dict[str, bool]):
        for color, state in states.items():
            self.set_led(color, state)

    def get_button_state(self, color: str) -> bool:
        btn = self.buttons.get(color)
        return btn.is_pressed() if btn and callable(getattr(btn, 'is_pressed', None)) else False

    def led_on(self, color: str):
        self.set_led(color, True)

    def led_off(self, color: str):
        self.set_led(color, False)

    def all_leds_off(self):
        for color in self.leds:
            self.set_led(color, False)

    def all_leds_on(self):
        for color in self.leds:
            self.set_led(color, True)

    def log_event(self, msg: str):
        if self.logger:
            self.logger.info(msg)
        if self.event_bus:
            self.event_bus.publish('app_event', {'message': msg})

    def display_text(self, text: str, **kwargs):
        # Try advanced display first
        if hasattr(self.screen, 'display_text') and callable(getattr(self.screen, 'display_text', None)):
            self.screen.display_text(text, **kwargs)
        # Fallback to print_line if available
        elif hasattr(self.screen, 'print_line') and callable(getattr(self.screen, 'print_line', None)):
            self.screen.print_line(text)
        # Fallback to clear + print_line
        elif hasattr(self.screen, 'clear') and callable(getattr(self.screen, 'clear', None)):
            self.screen.clear()
            if hasattr(self.screen, 'set_cursor') and callable(getattr(self.screen, 'set_cursor', None)):
                self.screen.set_cursor(0)
            if hasattr(self.screen, 'print_line') and callable(getattr(self.screen, 'print_line', None)):
                self.screen.print_line(text)

    def clear_screen(self):
        if hasattr(self.screen, 'clear') and callable(getattr(self.screen, 'clear', None)):
            self.screen.clear()

    def set_cursor(self, y: int = 0):
        if hasattr(self.screen, 'set_cursor') and callable(getattr(self.screen, 'set_cursor', None)):
            self.screen.set_cursor(y)
