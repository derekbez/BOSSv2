"""
Domain events for B.O.S.S. (relocated to boss.core.events)
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
import time


@dataclass
class DomainEvent:
    """Base class for all domain events."""
    event_type: str
    timestamp: float
    payload: Dict[str, Any]
    source: str
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


# Hardware Events
@dataclass
class SwitchChangedEvent(DomainEvent):
    """Fired when switch values change."""
    def __init__(self, old_value: int, new_value: int, source: str = "hardware"):
        super().__init__(
            event_type="switch_changed",
            timestamp=time.time(),
            payload={"old_value": old_value, "new_value": new_value},
            source=source
        )


@dataclass
class ButtonPressedEvent(DomainEvent):
    """Fired when a button is pressed."""
    def __init__(self, button_color: str, source: str = "hardware"):
        super().__init__(
            event_type="button_pressed",
            timestamp=time.time(),
            payload={"button": button_color},
            source=source
        )


@dataclass
class ButtonReleasedEvent(DomainEvent):
    """Fired when a button is released."""
    def __init__(self, button_color: str, source: str = "hardware"):
        super().__init__(
            event_type="button_released",
            timestamp=time.time(),
            payload={"button": button_color},
            source=source
        )


@dataclass
class GoButtonPressedEvent(DomainEvent):
    """Fired when the main Go button is pressed."""
    def __init__(self, source: str = "hardware"):
        super().__init__(
            event_type="go_button_pressed",
            timestamp=time.time(),
            payload={},
            source=source
        )


# App Events
@dataclass
class AppStartedEvent(DomainEvent):
    """Fired when an app starts running."""
    def __init__(self, app_name: str, switch_value: int, source: str = "app_manager"):
        super().__init__(
            event_type="app_started",
            timestamp=time.time(),
            payload={"app_name": app_name, "switch_value": switch_value},
            source=source
        )


@dataclass
class AppStoppedEvent(DomainEvent):
    """Fired when an app stops running."""
    def __init__(self, app_name: str, switch_value: int, reason: str = "normal", source: str = "app_manager"):
        super().__init__(
            event_type="app_stopped",
            timestamp=time.time(),
            payload={"app_name": app_name, "switch_value": switch_value, "reason": reason},
            source=source
        )


@dataclass
class AppErrorEvent(DomainEvent):
    """Fired when an app encounters an error."""
    def __init__(self, app_name: str, switch_value: int, error: str, source: str = "app_manager"):
        super().__init__(
            event_type="app_error",
            timestamp=time.time(),
            payload={"app_name": app_name, "switch_value": switch_value, "error": error},
            source=source
        )


# System Events
@dataclass
class SystemStartedEvent(DomainEvent):
    """Fired when the BOSS system starts."""
    def __init__(self, hardware_type: str, source: str = "system"):
        super().__init__(
            event_type="system_started",
            timestamp=time.time(),
            payload={"hardware_type": hardware_type},
            source=source
        )


@dataclass
class SystemShutdownEvent(DomainEvent):
    """Fired when the BOSS system is shutting down."""
    def __init__(self, reason: str = "user_request", source: str = "system"):
        super().__init__(
            event_type="system_shutdown",
            timestamp=time.time(),
            payload={"reason": reason},
            source=source
        )


# Display Events
@dataclass
class DisplayUpdateEvent(DomainEvent):
    """Fired when the display should be updated."""
    def __init__(self, value: Optional[int], brightness: float = 1.0, source: str = "system"):
        super().__init__(
            event_type="display_update",
            timestamp=time.time(),
            payload={"value": value, "brightness": brightness},
            source=source
        )


@dataclass
class LedUpdateEvent(DomainEvent):
    """Fired when an LED should be updated."""
    def __init__(self, color: str, is_on: bool, brightness: float = 1.0, source: str = "system"):
        super().__init__(
            event_type="led_update",
            timestamp=time.time(),
            payload={"color": color, "is_on": is_on, "brightness": brightness},
            source=source
        )


@dataclass
class ScreenUpdateEvent(DomainEvent):
    """Fired when the screen should be updated."""
    def __init__(self, content_type: str, content: Any, source: str = "app"):
        super().__init__(
            event_type="screen_update",
            timestamp=time.time(),
            payload={"content_type": content_type, "content": content},
            source=source
        )
