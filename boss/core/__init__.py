"""Core facade for flattened BOSS architecture.

Provides a simplified import surface while avoiding import-time
side effects that can cause circular imports. Symbols are lazily
resolved on first access via ``__getattr__``.
"""

__all__ = [
    "AppManager",
    "AppRunner",
    "HardwareManager",
    "SystemManager",
    "EventBus",
    "AppAPI",
]

def __getattr__(name: str):
    if name == "AppManager":
        from .app_manager import AppManager as _AppManager
        return _AppManager
    if name == "AppRunner":
        from .app_runner import AppRunner as _AppRunner
        return _AppRunner
    if name == "HardwareManager":
        from .hardware_manager import HardwareManager as _HardwareManager
        return _HardwareManager
    if name == "SystemManager":
        from .system_manager import SystemManager as _SystemManager
        return _SystemManager
    if name == "EventBus":
        from .event_bus import EventBus as _EventBus
        return _EventBus
    if name == "AppAPI":
        from .api import AppAPI as _AppAPI
        return _AppAPI
    raise AttributeError(f"module 'boss.core' has no attribute {name!r}")
