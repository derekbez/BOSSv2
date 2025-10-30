"""
Mock hardware implementations for testing.
"""

import logging
import threading
import time
from typing import Optional, Callable, Dict
from boss.core.interfaces.hardware import (
    ButtonInterface, GoButtonInterface, LedInterface, SwitchInterface, 
    DisplayInterface, ScreenInterface, SpeakerInterface
)
from boss.core.models import LedColor, ButtonColor, LedState, SwitchState

logger = logging.getLogger(__name__)


class MockButtons(ButtonInterface):
    """Mock button implementation."""
    
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
        """Initialize mock buttons."""
        self._available = True
        logger.debug("Mock buttons initialized")
        return True
    
    def cleanup(self) -> None:
        """Clean up mock buttons."""
        self._available = False
        logger.debug("Mock buttons cleaned up")
    
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
    
    def simulate_press(self, color: ButtonColor) -> None:
        """Simulate button press (for testing)."""
        if color in self._button_states:
            self._button_states[color] = True
            callback = self._press_callbacks.get(color)
            if callback:
                callback(color)
            logger.debug(f"Mock button {color.value} pressed")
    
    def simulate_release(self, color: ButtonColor) -> None:
        """Simulate button release (for testing)."""
        if color in self._button_states:
            self._button_states[color] = False
            callback = self._release_callbacks.get(color)
            if callback:
                callback(color)
            logger.debug(f"Mock button {color.value} released")


class MockGoButton(GoButtonInterface):
    """Mock Go button implementation."""
    
    def __init__(self):
        self._pressed = False
        self._press_callback: Optional[Callable] = None
        self._available = False
    
    def initialize(self) -> bool:
        """Initialize mock Go button."""
        self._available = True
        logger.debug("Mock Go button initialized")
        return True
    
    def cleanup(self) -> None:
        """Clean up mock Go button."""
        self._available = False
        logger.debug("Mock Go button cleaned up")
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def is_pressed(self) -> bool:
        """Check if the Go button is currently pressed."""
        return self._pressed
    
    def set_press_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for Go button press events."""
        self._press_callback = callback
    
    def simulate_press(self) -> None:
        """Simulate Go button press (for testing)."""
        self._pressed = True
        if self._press_callback:
            self._press_callback()
        logger.debug("Mock Go button pressed")
        
        # Auto-release after short delay
        def auto_release():
            time.sleep(0.1)
            self._pressed = False
        
        threading.Thread(target=auto_release, daemon=True).start()


class MockLeds(LedInterface):
    """Mock LED implementation."""
    
    def __init__(self):
        self._led_states: Dict[LedColor, LedState] = {
            color: LedState(color=color, is_on=False) for color in LedColor
        }
        self._available = False
    
    def initialize(self) -> bool:
        """Initialize mock LEDs."""
        self._available = True
        logger.debug("Mock LEDs initialized")
        return True
    
    def cleanup(self) -> None:
        """Clean up mock LEDs."""
        self._available = False
        logger.debug("Mock LEDs cleaned up")
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def set_led(self, color: LedColor, is_on: bool, brightness: float = 1.0) -> None:
        """Set LED state."""
        self._led_states[color] = LedState(color=color, is_on=is_on, brightness=brightness)
        logger.debug(f"Mock LED {color.value}: {'ON' if is_on else 'OFF'} (brightness: {brightness})")
    
    def get_led_state(self, color: LedColor) -> LedState:
        """Get current LED state."""
        return self._led_states[color]
    
    def set_all_leds(self, is_on: bool, brightness: float = 1.0) -> None:
        """Set all LEDs to the same state."""
        for color in LedColor:
            self.set_led(color, is_on, brightness)


class MockSwitches(SwitchInterface):
    """Mock switch implementation."""
    
    def __init__(self):
        self._switch_value = 0
        self._individual_switches = {i: False for i in range(8)}
        self._change_callback: Optional[Callable] = None
        self._available = False
    
    def initialize(self) -> bool:
        """Initialize mock switches."""
        self._available = True
        logger.debug("Mock switches initialized")
        return True
    
    def cleanup(self) -> None:
        """Clean up mock switches."""
        self._available = False
        logger.debug("Mock switches cleaned up")
    
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
    
    def simulate_switch_change(self, new_value: int) -> None:
        """Simulate switch change (for testing)."""
        if not 0 <= new_value <= 255:
            raise ValueError(f"Switch value must be 0-255, got {new_value}")
        
        old_value = self._switch_value
        self._switch_value = new_value
        
        # Update individual switches
        for i in range(8):
            self._individual_switches[i] = bool(new_value & (1 << i))
        
        if self._change_callback and old_value != new_value:
            self._change_callback(old_value, new_value)
        
        logger.debug(f"Mock switches changed: {old_value} -> {new_value}")


class MockDisplay(DisplayInterface):
    """Mock 7-segment display implementation."""
    
    def __init__(self):
        self._current_value: Optional[int] = None
        self._brightness = 1.0
        self._available = False
    
    def initialize(self) -> bool:
        """Initialize mock display."""
        self._available = True
        logger.debug("Mock display initialized")
        return True
    
    def cleanup(self) -> None:
        """Clean up mock display."""
        self._available = False
        logger.debug("Mock display cleaned up")
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def show_number(self, value: int, brightness: float = 1.0) -> None:
        """Display a number (0-9999)."""
        if not 0 <= value <= 9999:
            raise ValueError(f"Display value must be 0-9999, got {value}")
        
        self._current_value = value
        self._brightness = brightness
        logger.debug(f"Mock display: {value} (brightness: {brightness})")
    
    def show_text(self, text: str, brightness: float = 1.0) -> None:
        """Display text (limited characters)."""
        self._brightness = brightness
        logger.debug(f"Mock display text: '{text}' (brightness: {brightness})")
    
    def clear(self) -> None:
        """Clear the display."""
        self._current_value = None
        logger.debug("Mock display cleared")
    
    def set_brightness(self, brightness: float) -> None:
        """Set display brightness (0.0-1.0)."""
        self._brightness = brightness
        logger.debug(f"Mock display brightness: {brightness}")


class MockScreen(ScreenInterface):
    """Mock screen implementation."""
    
    def __init__(self, width: int = 800, height: int = 480):
        self._width = width
        self._height = height
        self._current_content = "BOSS Screen Ready"
        self._available = False
    
    def initialize(self) -> bool:
        """Initialize mock screen."""
        self._available = True
        logger.debug(f"Mock screen initialized ({self._width}x{self._height})")
        return True
    
    def cleanup(self) -> None:
        """Clean up mock screen."""
        self._available = False
        logger.debug("Mock screen cleaned up")
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def display_text(self, text: str, font_size: int = 24, color: str = "white", 
                    background: str = "black", align: str = "center", wrap: bool = True, wrap_width: int | None = None) -> None:
        """Display text on screen (with optional wrapping)."""
        processed = text
        if wrap:
            try:
                import textwrap
                eff_width = wrap_width
                if eff_width is None:
                    eff_width = getattr(self, 'screen_wrap_width_chars', 80)
                wrapped_lines = []
                for line in str(processed).splitlines():
                    wrapped_lines.extend(textwrap.wrap(line, width=int(eff_width)) or [""])
                processed = "\n".join(wrapped_lines)
            except Exception as e:
                logger.debug(f"Mock wrap failed: {e}")
        self._current_content = processed
        logger.info(f"Mock screen text: '{processed}' (size: {font_size}, color: {color}, align: {align})")
    
    def display_image(self, image_path: str, scale: float = 1.0, position: tuple = (0, 0)) -> None:
        """Display an image on screen."""
        self._current_content = f"Image: {image_path}"
        logger.info(f"Mock screen image: {image_path} (scale: {scale}, pos: {position})")
    
    def clear_screen(self, color: str = "black") -> None:
        """Clear screen with specified color."""
        self._current_content = f"Cleared ({color})"
        logger.debug(f"Mock screen cleared with color: {color}")
    
    def get_screen_size(self) -> tuple:
        """Get screen dimensions (width, height)."""
        return (self._width, self._height)


class MockSpeaker(SpeakerInterface):
    """Mock speaker implementation."""
    
    def __init__(self):
        self._volume = 1.0
        self._available = False
    
    def initialize(self) -> bool:
        """Initialize mock speaker."""
        self._available = True
        logger.debug("Mock speaker initialized")
        return True
    
    def cleanup(self) -> None:
        """Clean up mock speaker."""
        self._available = False
        logger.debug("Mock speaker cleaned up")
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def play_sound(self, sound_path: str, volume: float = 1.0) -> None:
        """Play a sound file."""
        logger.info(f"Mock speaker playing: {sound_path} (volume: {volume})")
    
    def play_tone(self, frequency: int, duration: float, volume: float = 1.0) -> None:
        """Play a tone at specified frequency and duration."""
        logger.info(f"Mock speaker tone: {frequency}Hz for {duration}s (volume: {volume})")
    
    def set_volume(self, volume: float) -> None:
        """Set speaker volume (0.0-1.0)."""
        self._volume = volume
        logger.debug(f"Mock speaker volume: {volume}")
