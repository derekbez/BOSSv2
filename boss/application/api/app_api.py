"""
App API implementation - The interface provided to mini-apps.
"""

import logging
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from boss.domain.interfaces.app_api import AppAPIInterface, EventBusInterface, ScreenAPIInterface, HardwareAPIInterface

logger = logging.getLogger(__name__)


class AppEventBus(EventBusInterface):
    """Event bus interface for mini-apps."""
    
    def __init__(self, event_bus, app_name: str):
        self._event_bus = event_bus
        self._app_name = app_name
        self._subscriptions = []  # Track subscriptions for cleanup
    
    def subscribe(self, event_type: str, handler: Callable, filter_dict: Optional[Dict[str, Any]] = None) -> str:
        """Subscribe to events."""
        subscription_id = self._event_bus.subscribe(event_type, handler, filter_dict)
        self._subscriptions.append(subscription_id)
        logger.debug(f"App {self._app_name} subscribed to {event_type}")
        return subscription_id
    
    def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from events."""
        self._event_bus.unsubscribe(subscription_id)
        if subscription_id in self._subscriptions:
            self._subscriptions.remove(subscription_id)
        logger.debug(f"App {self._app_name} unsubscribed {subscription_id}")
    
    def publish(self, event_type: str, payload: Dict[str, Any], source: str = "app") -> None:
        """Publish an event."""
        # Add app name to source
        full_source = f"{source}:{self._app_name}"
        self._event_bus.publish(event_type, payload, full_source)
    
    def cleanup(self) -> None:
        """Clean up all subscriptions when app stops."""
        for subscription_id in self._subscriptions:
            try:
                self._event_bus.unsubscribe(subscription_id)
            except Exception as e:
                logger.error(f"Error cleaning up subscription {subscription_id}: {e}")
        self._subscriptions.clear()


class AppScreenAPI(ScreenAPIInterface):
    """Screen interface for mini-apps."""
    
    def __init__(self, event_bus, app_name: str):
        self._event_bus = event_bus
        self._app_name = app_name
    
    def display_text(self, text: str, font_size: int = 24, color: str = "white", 
                    background: str = "black", align: str = "center") -> None:
        """Display text on screen."""
        self._event_bus.publish("screen_update", {
            "content_type": "text",
            "content": text,
            "font_size": font_size,
            "color": color,
            "background": background,
            "align": align
        }, f"app:{self._app_name}")
    
    def display_image(self, image_path: str, scale: float = 1.0, position: tuple = (0, 0)) -> None:
        """Display an image on screen."""
        self._event_bus.publish("screen_update", {
            "content_type": "image",
            "content": image_path,
            "scale": scale,
            "position": position
        }, f"app:{self._app_name}")
    
    def clear_screen(self, color: str = "black") -> None:
        """Clear screen with specified color."""
        self._event_bus.publish("screen_update", {
            "content_type": "clear",
            "content": color
        }, f"app:{self._app_name}")
    
    def get_screen_size(self) -> tuple:
        """Get screen dimensions (width, height)."""
        # This could be retrieved from hardware service, for now return default
        return (800, 480)


class AppHardwareAPI(HardwareAPIInterface):
    """Hardware interface for mini-apps."""
    
    def __init__(self, event_bus, app_name: str):
        self._event_bus = event_bus
        self._app_name = app_name
    
    def set_led(self, color: str, is_on: bool, brightness: float = 1.0) -> None:
        """Set LED state."""
        valid_colors = ["red", "yellow", "green", "blue"]
        if color not in valid_colors:
            raise ValueError(f"Invalid LED color: {color}. Must be one of {valid_colors}")
        
        if not 0.0 <= brightness <= 1.0:
            raise ValueError(f"LED brightness must be 0.0-1.0, got {brightness}")
        
        self._event_bus.publish("led_update", {
            "color": color,
            "is_on": is_on,
            "brightness": brightness
        }, f"app:{self._app_name}")
    
    def set_display(self, value: Optional[int], brightness: float = 1.0) -> None:
        """Set 7-segment display value."""
        if value is not None and not 0 <= value <= 9999:
            raise ValueError(f"Display value must be 0-9999 or None, got {value}")
        
        if not 0.0 <= brightness <= 1.0:
            raise ValueError(f"Display brightness must be 0.0-1.0, got {brightness}")
        
        self._event_bus.publish("display_update", {
            "value": value,
            "brightness": brightness
        }, f"app:{self._app_name}")
    
    def play_sound(self, sound_path: str, volume: float = 1.0) -> None:
        """Play a sound file."""
        if not 0.0 <= volume <= 1.0:
            raise ValueError(f"Volume must be 0.0-1.0, got {volume}")
        
        # This would be handled by hardware service
        logger.info(f"App {self._app_name} requested sound: {sound_path}")


class AppAPI(AppAPIInterface):
    """Complete API implementation provided to mini-apps."""
    
    def __init__(self, event_bus, app_name: str, app_path: Path, app_manager=None):
        self._app_name = app_name
        self._app_path = app_path
        self._app_manager = app_manager
        
        # Create sub-interfaces
        self._event_bus = AppEventBus(event_bus, app_name)
        self._screen = AppScreenAPI(event_bus, app_name)
        self._hardware = AppHardwareAPI(event_bus, app_name)
    
    @property
    def event_bus(self) -> EventBusInterface:
        """Access to the event bus."""
        return self._event_bus
    
    @property
    def screen(self) -> ScreenAPIInterface:
        """Access to screen control."""
        return self._screen
    
    @property
    def hardware(self) -> HardwareAPIInterface:
        """Access to limited hardware control."""
        return self._hardware
    
    def get_app_path(self) -> str:
        """Get the path to the current app directory."""
        return str(self._app_path)
    
    def get_asset_path(self, filename: str) -> str:
        """Get the full path to an app asset file."""
        assets_dir = self._app_path / "assets"
        asset_path = assets_dir / filename
        return str(asset_path)
    
    def log_info(self, message: str) -> None:
        """Log an info message."""
        logger.info(f"[{self._app_name}] {message}")
    
    def log_error(self, message: str) -> None:
        """Log an error message."""
        logger.error(f"[{self._app_name}] {message}")
    
    def get_all_apps(self) -> list:
        """Get list of all available apps."""
        if self._app_manager is None:
            logger.warning(f"App {self._app_name} requested all apps but app_manager not available")
            return []
        
        try:
            return self._app_manager.get_all_apps()
        except Exception as e:
            logger.error(f"Error getting all apps for {self._app_name}: {e}")
            return []
    
    def cleanup(self) -> None:
        """Clean up API resources when app stops."""
        self._event_bus.cleanup()
