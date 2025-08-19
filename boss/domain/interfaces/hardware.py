"""
Hardware abstraction interfaces for B.O.S.S.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from ..models.hardware_state import LedColor, ButtonColor, LedState, ButtonState, DisplayState, SwitchState


class HardwareComponent(ABC):
    """Base interface for all hardware components."""
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the hardware component. Returns True if successful."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up hardware resources."""
        pass
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if hardware is available and functioning."""
        pass


class ButtonInterface(HardwareComponent):
    """Interface for button hardware."""
    
    @abstractmethod
    def is_pressed(self, color: ButtonColor) -> bool:
        """Check if a button is currently pressed."""
        pass
    
    @abstractmethod
    def set_press_callback(self, color: ButtonColor, callback: Callable[[ButtonColor], None]) -> None:
        """Set callback for button press events."""
        pass
    
    @abstractmethod
    def set_release_callback(self, color: ButtonColor, callback: Callable[[ButtonColor], None]) -> None:
        """Set callback for button release events."""
        pass


class GoButtonInterface(HardwareComponent):
    """Interface for the main Go button."""
    
    @abstractmethod
    def is_pressed(self) -> bool:
        """Check if the Go button is currently pressed."""
        pass
    
    @abstractmethod
    def set_press_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for Go button press events."""
        pass


class LedInterface(HardwareComponent):
    """Interface for LED hardware."""
    
    @abstractmethod
    def set_led(self, color: LedColor, is_on: bool, brightness: float = 1.0) -> None:
        """Set LED state."""
        pass
    
    @abstractmethod
    def get_led_state(self, color: LedColor) -> LedState:
        """Get current LED state."""
        pass
    
    @abstractmethod
    def set_all_leds(self, is_on: bool, brightness: float = 1.0) -> None:
        """Set all LEDs to the same state."""
        pass


class SwitchInterface(HardwareComponent):
    """Interface for switch array hardware."""
    
    @abstractmethod
    def read_switches(self) -> SwitchState:
        """Read current switch state."""
        pass
    
    @abstractmethod
    def set_change_callback(self, callback: Callable[[int, int], None]) -> None:
        """Set callback for switch change events (old_value, new_value)."""
        pass


class DisplayInterface(HardwareComponent):
    """Interface for 7-segment display hardware."""
    
    @abstractmethod
    def show_number(self, value: int, brightness: float = 1.0) -> None:
        """Display a number (0-9999)."""
        pass
    
    @abstractmethod
    def show_text(self, text: str, brightness: float = 1.0) -> None:
        """Display text (limited characters)."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear the display."""
        pass
    
    @abstractmethod
    def set_brightness(self, brightness: float) -> None:
        """Set display brightness (0.0-1.0)."""
        pass


class ScreenInterface(HardwareComponent):
    """Interface for main screen hardware."""
    
    @abstractmethod
    def display_text(self, text: str, font_size: int = 24, color: str = "white", 
                    background: str = "black", align: str = "center") -> None:
        """Display text on screen."""
        pass
    
    @abstractmethod
    def display_image(self, image_path: str, scale: float = 1.0, position: tuple = (0, 0)) -> None:
        """Display an image on screen."""
        pass
    
    @abstractmethod
    def clear_screen(self, color: str = "black") -> None:
        """Clear screen with specified color."""
        pass
    
    @abstractmethod
    def get_screen_size(self) -> tuple:
        """Get screen dimensions (width, height)."""
        pass


class SpeakerInterface(HardwareComponent):
    """Interface for speaker hardware."""
    
    @abstractmethod
    def play_sound(self, sound_path: str, volume: float = 1.0) -> None:
        """Play a sound file."""
        pass
    
    @abstractmethod
    def play_tone(self, frequency: int, duration: float, volume: float = 1.0) -> None:
        """Play a tone at specified frequency and duration."""
        pass
    
    @abstractmethod
    def set_volume(self, volume: float) -> None:
        """Set speaker volume (0.0-1.0)."""
        pass


class HardwareFactory(ABC):
    """Factory interface for creating hardware implementations."""
    
    @abstractmethod
    def create_buttons(self) -> ButtonInterface:
        """Create button interface implementation."""
        pass
    
    @abstractmethod
    def create_go_button(self) -> GoButtonInterface:
        """Create Go button interface implementation."""
        pass
    
    @abstractmethod
    def create_leds(self) -> LedInterface:
        """Create LED interface implementation."""
        pass
    
    @abstractmethod
    def create_switches(self) -> SwitchInterface:
        """Create switch interface implementation."""
        pass
    
    @abstractmethod
    def create_display(self) -> DisplayInterface:
        """Create display interface implementation."""
        pass
    
    @abstractmethod
    def create_screen(self) -> ScreenInterface:
        """Create screen interface implementation."""
        pass
    
    @abstractmethod
    def create_speaker(self) -> Optional[SpeakerInterface]:
        """Create speaker interface implementation. Returns None if not available."""
        pass
    
    @property
    @abstractmethod
    def hardware_type(self) -> str:
        """Get the type of hardware implementation (gpio, webui, mock)."""
        pass

    # --- Optional hooks to preserve presentation/application parity ---
    # Default implementations are no-ops; concrete factories may override.
    def attach_event_bus(self, event_bus, components: Optional[Dict[str, Any]] = None) -> None:
        """Attach event bus to components when applicable (e.g., WebUI).

        Args:
            event_bus: The central event bus instance.
            components: Optional map of component name to instance.
        """
        return None

    def start_dev_ui(self, event_bus, components: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """Start a development UI if supported by the factory (no-op otherwise).

        Returns an optional port number or None if not applicable.
        """
        return None

    def stop_dev_ui(self) -> None:
        """Stop any development UI started by start_dev_ui (no-op by default)."""
        return None
