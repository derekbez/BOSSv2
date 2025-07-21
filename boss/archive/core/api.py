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

    def __init__(self, screen, buttons: Dict[str, Any], leds: Dict[str, Any], display=None, switch_reader=None, event_bus=None, logger=None):
        self.screen = screen
        self.buttons = buttons  # dict: color -> button instance
        self.leds = leds        # dict: color -> led instance
        self.display = display  # 7-segment display
        self.switch_reader = switch_reader  # switch reader for current value
        self.event_bus = event_bus
        self.logger = logger

    # --- Button Methods ---
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

    def get_button_state(self, color: str) -> bool:
        """Get the current state of a button."""
        btn = self.buttons.get(color)
        return btn.is_pressed() if btn and callable(getattr(btn, 'is_pressed', None)) else False

    # --- LED Control Methods ---
    def set_led(self, color: str, state: bool):
        """Set the state of a single LED."""
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
        """Set the state of multiple LEDs."""
        for color, state in states.items():
            self.set_led(color, state)

    def led_on(self, color: str):
        """Turn on a specific LED."""
        self.set_led(color, True)

    def led_off(self, color: str):
        """Turn off a specific LED."""
        self.set_led(color, False)

    def all_leds_off(self):
        """Turn off all LEDs."""
        for color in self.leds:
            self.set_led(color, False)

    def all_leds_on(self):
        """Turn on all LEDs."""
        for color in self.leds:
            self.set_led(color, True)

    def get_led_state(self, color: str) -> bool:
        """Get the current state of an LED."""
        led = self.leds.get(color)
        if led and callable(getattr(led, 'is_on', None)):
            return led.is_on()
        return False

    # --- 7-Segment Display Methods ---
    def set_display(self, value) -> bool:
        """
        Set the 7-segment display to show a number or message.
        Args:
            value: int (0-9999) or str (up to 4 chars)
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.display:
            return False
        try:
            if isinstance(value, (int, float)):
                if callable(getattr(self.display, 'show_number', None)):
                    self.display.show_number(int(value))
                    return True
            else:
                if callable(getattr(self.display, 'show_message', None)):
                    self.display.show_message(str(value))
                    return True
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to set display: {e}")
        return False

    def clear_display(self) -> bool:
        """Clear the 7-segment display."""
        return self.set_display("    ")

    # --- Switch Reading Methods ---
    def get_switch_value(self) -> int:
        """
        Get the current value from the toggle switches (0-255).
        Returns 0 if switch reader is not available.
        """
        if self.switch_reader and callable(getattr(self.switch_reader, 'read_value', None)):
            try:
                return self.switch_reader.read_value()
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Failed to read switch value: {e}")
        return 0

    # --- Screen Methods ---
    def display_text(self, text: str, **kwargs):
        """Display text on the main screen with formatting options."""
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
        """Clear the main screen."""
        if hasattr(self.screen, 'clear') and callable(getattr(self.screen, 'clear', None)):
            self.screen.clear()

    def set_cursor(self, y: int = 0):
        """Set the cursor position on the screen."""
        if hasattr(self.screen, 'set_cursor') and callable(getattr(self.screen, 'set_cursor', None)):
            self.screen.set_cursor(y)

    # --- Configuration and Logging Methods ---
    def get_app_config(self, app_name: Optional[str] = None, default: Optional[Dict] = None) -> Dict:
        """
        Get configuration for a mini-app.
        Args:
            app_name: Name of the app (auto-detected if None)
            default: Default configuration to return if not found
        Returns:
            Dict: App configuration or default
        """
        if default is None:
            default = {}
        
        # For now, return default config
        # TODO: Implement proper config loading from files
        return default.copy()

    def log_event(self, msg: str):
        """Log an event message."""
        if self.logger:
            self.logger.info(msg)
        if self.event_bus:
            self.event_bus.publish('app_event', {'message': msg})

    def log_info(self, msg: str):
        """Log an info message."""
        if self.logger:
            self.logger.info(msg)

    def log_warning(self, msg: str):
        """Log a warning message."""
        if self.logger:
            self.logger.warning(msg)

    def log_error(self, msg: str):
        """Log an error message."""
        if self.logger:
            self.logger.error(msg)

    # --- Hardware Status Methods ---
    def get_hardware_status(self) -> Dict[str, bool]:
        """
        Get the status of all hardware components.
        Returns:
            Dict: Hardware component availability status
        """
        status = {
            'screen': self.screen is not None,
            'display': self.display is not None,
            'switch_reader': self.switch_reader is not None,
            'event_bus': self.event_bus is not None,
            'logger': self.logger is not None,
        }
        
        # Check individual buttons and LEDs
        for color in ['red', 'yellow', 'green', 'blue']:
            status[f'button_{color}'] = color in self.buttons and self.buttons[color] is not None
            status[f'led_{color}'] = color in self.leds and self.leds[color] is not None
            
        return status

    # --- Event Bus Integration ---
    def subscribe_event(self, event_type: str, handler, filter_dict: Optional[Dict] = None):
        """
        Subscribe to an event with optional filtering.
        Returns subscription ID for unsubscribing.
        """
        if self.event_bus and callable(getattr(self.event_bus, 'subscribe', None)):
            return self.event_bus.subscribe(event_type, handler, filter=filter_dict)
        return None

    def unsubscribe_event(self, subscription_id):
        """Unsubscribe from an event using subscription ID."""
        if self.event_bus and callable(getattr(self.event_bus, 'unsubscribe', None)):
            self.event_bus.unsubscribe(subscription_id)

    def publish_event(self, event_type: str, payload: Dict):
        """Publish an event to the event bus."""
        if self.event_bus and callable(getattr(self.event_bus, 'publish', None)):
            self.event_bus.publish(event_type, payload)
