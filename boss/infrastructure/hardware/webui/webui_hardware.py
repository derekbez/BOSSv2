"""
WebUI hardware implementations for development.
"""

import logging
import threading
import time
from typing import Optional, Callable, Dict
from boss.domain.interfaces.hardware import (
    ButtonInterface, GoButtonInterface, LedInterface, SwitchInterface, 
    DisplayInterface, ScreenInterface, SpeakerInterface
)
from boss.domain.models.hardware_state import LedColor, ButtonColor, LedState, SwitchState

logger = logging.getLogger(__name__)


class WebUIButtons(ButtonInterface):
    """WebUI button implementation - simulates buttons in web interface."""
    
    def __init__(self):
        self._button_states: Dict[ButtonColor, bool] = {
            color: False for color in ButtonColor
        }
        self._press_callbacks: Dict[ButtonColor, Optional[Callable]] = {
            color: None for color in ButtonColor
        }
        self._release_callbacks: Dict[ButtonColor, Optional[Callable]] = {
            color: None for color in ButtonColor
        }
        self._available = False
    
    def initialize(self) -> bool:
        """Initialize WebUI buttons."""
        self._available = True
        logger.info("WebUI buttons initialized - check web interface for controls")
        return True
    
    def cleanup(self) -> None:
        """Clean up WebUI buttons."""
        self._available = False
        logger.debug("WebUI buttons cleaned up")
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def is_pressed(self, color: ButtonColor) -> bool:
        """Check if a button is currently pressed."""
        return self._button_states.get(color, False)
    
    def set_press_callback(self, color: ButtonColor, callback: Callable[[ButtonColor], None]) -> None:
        """Set callback for button press events."""
        self._press_callbacks[color] = callback
    
    def set_release_callback(self, color: ButtonColor, callback: Callable[[ButtonColor], None]) -> None:
        """Set callback for button release events."""
        self._release_callbacks[color] = callback
    
    def handle_button_press(self, color_str: str) -> None:
        """Handle button press from web interface."""
        try:
            color = ButtonColor(color_str)
            self._button_states[color] = True
            callback = self._press_callbacks.get(color)
            if callback:
                callback(color)
            logger.debug(f"WebUI button {color.value} pressed")
        except ValueError:
            logger.error(f"Invalid button color from WebUI: {color_str}")
    
    def handle_button_release(self, color_str: str) -> None:
        """Handle button release from web interface."""
        try:
            color = ButtonColor(color_str)
            self._button_states[color] = False
            callback = self._release_callbacks.get(color)
            if callback:
                callback(color)
            logger.debug(f"WebUI button {color.value} released")
        except ValueError:
            logger.error(f"Invalid button color from WebUI: {color_str}")


class WebUIGoButton(GoButtonInterface):
    """WebUI Go button implementation."""
    
    def __init__(self):
        self._pressed = False
        self._press_callback: Optional[Callable] = None
        self._available = False
    
    def initialize(self) -> bool:
        """Initialize WebUI Go button."""
        self._available = True
        logger.info("WebUI Go button initialized")
        return True
    
    def cleanup(self) -> None:
        """Clean up WebUI Go button."""
        self._available = False
        logger.debug("WebUI Go button cleaned up")
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def is_pressed(self) -> bool:
        """Check if the Go button is currently pressed."""
        return self._pressed
    
    def set_press_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for Go button press events."""
        self._press_callback = callback
    
    def handle_press(self) -> None:
        """Handle Go button press from web interface."""
        self._pressed = True
        if self._press_callback:
            self._press_callback()
        logger.debug("WebUI Go button pressed")
        
        # Auto-release after short delay
        def auto_release():
            time.sleep(0.1)
            self._pressed = False
        
        threading.Thread(target=auto_release, daemon=True).start()


class WebUILeds(LedInterface):
    """WebUI LED implementation - shows LED states in web interface."""
    
    def __init__(self, event_bus=None):
        self._led_states: Dict[LedColor, LedState] = {
            color: LedState(color=color, is_on=False) for color in LedColor
        }
        self._available = False
        self._event_bus = event_bus
    
    def set_event_bus(self, event_bus):
        """Set the event bus for publishing LED state changes."""
        self._event_bus = event_bus
    
    def initialize(self) -> bool:
        """Initialize WebUI LEDs."""
        self._available = True
        logger.info("WebUI LEDs initialized - LED states will show in web interface")
        return True
    
    def cleanup(self) -> None:
        """Clean up WebUI LEDs."""
        self._available = False
        logger.debug("WebUI LEDs cleaned up")
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def set_led(self, color: LedColor, is_on: bool, brightness: float = 1.0) -> None:
        """Set LED state and publish to WebUI."""
        self._led_states[color] = LedState(color=color, is_on=is_on, brightness=brightness)
        logger.debug(f"WebUI LED {color.value}: {'ON' if is_on else 'OFF'} (brightness: {brightness})")
        
        # Publish event for WebUI update
        if self._event_bus:
            self._event_bus.publish("output.led.state_changed", {
                "led_id": color.value,
                "state": "on" if is_on else "off",
                "brightness": brightness
            })
    
    def get_led_state(self, color: LedColor) -> LedState:
        """Get current LED state."""
        return self._led_states[color]
    
    def set_all_leds(self, is_on: bool, brightness: float = 1.0) -> None:
        """Set all LEDs to the same state."""
        for color in LedColor:
            self.set_led(color, is_on, brightness)


class WebUISwitches(SwitchInterface):
    """WebUI switch implementation - switches controlled via web interface."""
    
    def __init__(self):
        self._switch_value = 0
        self._individual_switches = {i: False for i in range(8)}
        self._change_callback: Optional[Callable] = None
        self._available = False
    
    def initialize(self) -> bool:
        """Initialize WebUI switches."""
        self._available = True
        logger.info("WebUI switches initialized - use web interface to change switch values")
        return True
    
    def cleanup(self) -> None:
        """Clean up WebUI switches."""
        self._available = False
        logger.debug("WebUI switches cleaned up")
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def read_switches(self) -> SwitchState:
        """Read current switch state."""
        return SwitchState(
            value=self._switch_value,
            individual_switches=self._individual_switches.copy()
        )
    
    def set_change_callback(self, callback: Callable[[int, int], None]) -> None:
        """Set callback for switch change events."""
        self._change_callback = callback
    
    def handle_switch_change(self, new_value: int) -> None:
        """Handle switch change from web interface."""
        if not 0 <= new_value <= 255:
            logger.error(f"Invalid switch value from WebUI: {new_value}")
            return
        
        old_value = self._switch_value
        self._switch_value = new_value
        
        # Update individual switches
        for i in range(8):
            self._individual_switches[i] = bool(new_value & (1 << i))
        
        if self._change_callback and old_value != new_value:
            self._change_callback(old_value, new_value)
        
        logger.debug(f"WebUI switches changed: {old_value} -> {new_value}")


class WebUIDisplay(DisplayInterface):
    """WebUI 7-segment display implementation."""
    
    def __init__(self, event_bus=None):
        self._current_value: Optional[int] = None
        self._brightness = 1.0
        self._available = False
        self._event_bus = event_bus
    
    def set_event_bus(self, event_bus):
        """Set the event bus for publishing display updates."""
        self._event_bus = event_bus
    
    def initialize(self) -> bool:
        """Initialize WebUI display."""
        self._available = True
        logger.info("WebUI display initialized - display will show in web interface")
        return True
    
    def cleanup(self) -> None:
        """Clean up WebUI display."""
        self._available = False
        logger.debug("WebUI display cleaned up")
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def show_number(self, value: int, brightness: float = 1.0) -> None:
        """Display a number (0-9999)."""
        if not 0 <= value <= 9999:
            raise ValueError(f"Display value must be 0-9999, got {value}")
        
        self._current_value = value
        self._brightness = brightness
        logger.debug(f"WebUI display: {value} (brightness: {brightness})")
        
        # Publish event for WebUI update
        if self._event_bus:
            # Only emit the output.display.updated event; the canonical display_update
            # is published by the system when switches change. Avoid duplicate/legacy
            # events that can cause transient UI state.
            self._event_bus.publish("output.display.updated", {
                "type": "number",
                "value": value,
                "brightness": brightness,
                "text": str(value)
            })
    
    def show_text(self, text: str, brightness: float = 1.0) -> None:
        """Display text (limited characters)."""
        self._brightness = brightness
        logger.debug(f"WebUI display text: '{text}' (brightness: {brightness})")
        
        # Publish event for WebUI update
        if self._event_bus:
            self._event_bus.publish("output.display.updated", {
                "type": "text",
                "text": text,
                "brightness": brightness
            })
    
    def clear(self) -> None:
        """Clear the display."""
        self._current_value = None
        logger.debug("WebUI display cleared")
        
        # Publish event for WebUI update
        if self._event_bus:
            self._event_bus.publish("output.display.updated", {
                "type": "clear",
                "text": "",
                "brightness": self._brightness
            })
    
    def set_brightness(self, brightness: float) -> None:
        """Set display brightness (0.0-1.0)."""
        self._brightness = brightness
        logger.debug(f"WebUI display brightness: {brightness}")
        
        # Publish event for WebUI update
        if self._event_bus:
            self._event_bus.publish("output.display.updated", {
                "type": "brightness",
                "brightness": brightness,
                "text": str(self._current_value) if self._current_value is not None else ""
            })


class WebUIScreen(ScreenInterface):
    """WebUI screen implementation - shows screen content in web interface."""
    
    def __init__(self, width: int = 800, height: int = 480, event_bus=None):
        self._width = width
        self._height = height
        self._current_content = "BOSS WebUI Screen Ready"
        self._available = False
        self._event_bus = event_bus
    
    def set_event_bus(self, event_bus):
        """Set the event bus for publishing screen updates."""
        self._event_bus = event_bus
    
    def initialize(self) -> bool:
        """Initialize WebUI screen."""
        self._available = True
        logger.info(f"WebUI screen initialized ({self._width}x{self._height}) - content will show in web interface")
        return True
    
    def cleanup(self) -> None:
        """Clean up WebUI screen."""
        self._available = False
        logger.debug("WebUI screen cleaned up")
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def display_text(self, text: str, font_size: int = 24, color: str = "white", 
                    background: str = "black", align: str = "center") -> None:
        """Display text on screen."""
        self._current_content = text
        
        # Publish event for WebUI update - use the correct event that WebSocket manager listens for
        if self._event_bus:
            self._event_bus.publish("output.screen.updated", {
                "text": text,
                "font_size": font_size,
                "color": color,
                "background": background,
                "align": align,
                "content_type": "text"
            }, "webui_screen")
        
        logger.info(f"WebUI screen text updated: '{text}' (size: {font_size}, color: {color}, align: {align})")
    
    def display_image(self, image_path: str, scale: float = 1.0, position: tuple = (0, 0)) -> None:
        """Display an image on screen."""
        self._current_content = f"Image: {image_path}"
        
        # Publish event for WebUI update
        if self._event_bus:
            self._event_bus.publish("output.screen.updated", {
                "image_path": image_path,
                "scale": scale,
                "position": position,
                "content_type": "image"
            }, "webui_screen")
        
        logger.info(f"WebUI screen image: {image_path} (scale: {scale}, pos: {position})")
    
    def clear_screen(self, color: str = "black") -> None:
        """Clear screen with specified color."""
        self._current_content = ""
        
        # Publish event for WebUI update
        if self._event_bus:
            self._event_bus.publish("output.screen.updated", {
                "text": "",
                "color": color,
                "content_type": "clear"
            }, "webui_screen")
        
        logger.info(f"WebUI screen cleared with color: {color}")
    
    def get_screen_size(self) -> tuple:
        """Get screen dimensions (width, height)."""
        return (self._width, self._height)


class WebUISpeaker(SpeakerInterface):
    """WebUI speaker implementation - audio playback in web interface."""
    
    def __init__(self):
        self._volume = 1.0
        self._available = False
    
    def initialize(self) -> bool:
        """Initialize WebUI speaker."""
        self._available = True
        logger.info("WebUI speaker initialized - audio will play in web interface")
        return True
    
    def cleanup(self) -> None:
        """Clean up WebUI speaker."""
        self._available = False
        logger.debug("WebUI speaker cleaned up")
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def play_sound(self, sound_path: str, volume: float = 1.0) -> None:
        """Play a sound file."""
        logger.info(f"WebUI speaker playing: {sound_path} (volume: {volume})")
        # TODO: Send to web interface for audio playback
    
    def play_tone(self, frequency: int, duration: float, volume: float = 1.0) -> None:
        """Play a tone at specified frequency and duration."""
        logger.info(f"WebUI speaker tone: {frequency}Hz for {duration}s (volume: {volume})")
        # TODO: Generate tone in web interface
    
    def set_volume(self, volume: float) -> None:
        """Set speaker volume (0.0-1.0)."""
        self._volume = volume
        logger.debug(f"WebUI speaker volume: {volume}")
