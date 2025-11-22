"""Core facade for flattened BOSS architecture.

Provides a simplified, explicit import surface for core components.
"""

__all__ = [
    "AppManager",
    "AppRunner",
    "HardwareManager",
    "SystemManager",
    "EventBus",
    "AppAPI",
]

from .app_manager import AppManager
from .app_runner import AppRunner
from .hardware_manager import HardwareManager
from .system_manager import SystemManager
from .event_bus import EventBus
from .api import AppAPI
