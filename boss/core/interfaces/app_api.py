"""
App API interfaces (relocated to boss.core.interfaces).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable


class EventBusInterface(ABC):
    """Interface for the event bus accessible to mini-apps."""
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable, filter_dict: Optional[Dict[str, Any]] = None) -> str:
        """
        Subscribe to events.
        Returns subscription ID for unsubscribing.
        """
        pass
    
    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from events."""
        pass
    
    @abstractmethod
    def publish(self, event_type: str, payload: Dict[str, Any], source: str = "app") -> None:
        """Publish an event."""
        pass


class ScreenAPIInterface(ABC):
    """Interface for screen control accessible to mini-apps."""
    
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


class HardwareAPIInterface(ABC):
    """Interface for limited hardware control accessible to mini-apps."""
    
    @abstractmethod
    def set_led(self, color: str, is_on: bool, brightness: float = 1.0) -> None:
        """Set LED state."""
        pass
    
    @abstractmethod
    def set_display(self, value: Optional[int], brightness: float = 1.0) -> None:
        """Set 7-segment display value."""
        pass
    
    @abstractmethod
    def play_sound(self, sound_path: str, volume: float = 1.0) -> None:
        """Play a sound file."""
        pass


class AppAPIInterface(ABC):
    """Complete API interface provided to mini-apps."""
    
    @property
    @abstractmethod
    def event_bus(self) -> EventBusInterface:
        """Access to the event bus."""
        pass
    
    @property
    @abstractmethod
    def screen(self) -> ScreenAPIInterface:
        """Access to screen control."""
        pass
    
    @property
    @abstractmethod
    def hardware(self) -> HardwareAPIInterface:
        """Access to limited hardware control."""
        pass
    
    @abstractmethod
    def get_app_path(self) -> str:
        """Get the path to the current app directory."""
        pass
    
    @abstractmethod
    def get_asset_path(self, filename: str) -> str:
        """Get the full path to an app asset file."""
        pass
    
    @abstractmethod
    def get_app_asset_path(self) -> str:
        """Get the path to the app's assets directory."""
        pass
    
    @abstractmethod
    def log_info(self, message: str) -> None:
        """Log an info message."""
        pass
    
    @abstractmethod
    def log_error(self, message: str) -> None:
        """Log an error message."""
        pass
    
    @abstractmethod
    def get_all_apps(self) -> list:
        """Get list of all available apps. Returns list of App objects."""
        pass

    # Optional convenience helpers -----------------
    @abstractmethod
    def get_config_value(self, key: str, default: Any = None) -> Any:  # type: ignore[name-defined]
        """Return a single value from the app's manifest config (or default)."""
        pass

    @abstractmethod
    def get_app_config(self, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:  # type: ignore[name-defined]
        """Return the full config dict from the manifest (or provided default)."""
        pass
