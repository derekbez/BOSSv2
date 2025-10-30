"""Flat re-exports for domain models.

This allows importing core models via `from boss.core.models import App, AppManifest, AppStatus,
HardwareConfig, SystemConfig, BossConfig, HardwareState types` without referencing
boss.domain.* directly.
"""

from .app import App, AppManifest, AppStatus
from .config import HardwareConfig, SystemConfig, BossConfig
from .hardware_state import *  # LedColor, ButtonColor, LedState, SwitchState

__all__ = [
    "App",
    "AppManifest",
    "AppStatus",
    "HardwareConfig",
    "SystemConfig",
    "BossConfig",
    # hardware_state exports are wildcarded for convenience
]
