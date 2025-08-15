"""
Service interfaces for B.O.S.S.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from ..models.app import App, AppStatus
from ..models.hardware_state import HardwareState


class EventBusService(ABC):
    """Interface for the event bus service."""
    
    @abstractmethod
    def start(self) -> None:
        """Start the event bus service."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the event bus service."""
        pass
    
    @abstractmethod
    def publish(self, event_type: str, payload: Dict, source: str = "system") -> None:
        """Publish an event."""
        pass
    
    @abstractmethod
    def subscribe(self, event_type: str, handler, filter_dict: Optional[Dict] = None) -> str:
        """Subscribe to events. Returns subscription ID."""
        pass
    
    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from events."""
        pass


class AppManagerService(ABC):
    """Interface for the app manager service."""
    
    @abstractmethod
    def load_apps(self) -> None:
        """Load all available apps from the apps directory."""
        pass
    
    @abstractmethod
    def get_app_by_switch_value(self, switch_value: int) -> Optional[App]:
        """Get the app mapped to a switch value."""
        pass
    
    @abstractmethod
    def get_all_apps(self) -> Dict[int, App]:
        """Get all loaded apps."""
        pass
    
    @abstractmethod
    def get_current_app(self) -> Optional[App]:
        """Get the currently running app."""
        pass


class AppRunnerService(ABC):
    """Interface for the app runner service."""
    
    @abstractmethod
    def start_app(self, app: App) -> None:
        """Start running an app."""
        pass
    
    @abstractmethod
    def stop_current_app(self, *args, **kwargs) -> bool:
        """Stop the currently running app. Returns True if stopped within timeout."""
        pass
    
    @abstractmethod
    def get_running_app(self) -> Optional[App]:
        """Get the currently running app."""
        pass


class HardwareService(ABC):
    """Interface for the hardware service."""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize all hardware components."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up all hardware resources."""
        pass
    
    @abstractmethod
    def get_hardware_state(self) -> HardwareState:
        """Get current state of all hardware."""
        pass
    
    @abstractmethod
    def start_monitoring(self) -> None:
        """Start monitoring hardware for changes."""
        pass
    
    @abstractmethod
    def stop_monitoring(self) -> None:
        """Stop monitoring hardware."""
        pass


class SystemService(ABC):
    """Interface for the system service."""
    
    @abstractmethod
    def start(self) -> None:
        """Start the BOSS system."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the BOSS system."""
        pass
    
    @abstractmethod
    def restart(self) -> None:
        """Restart the BOSS system."""
        pass
    
    @abstractmethod
    def get_system_status(self) -> Dict:
        """Get current system status."""
        pass
