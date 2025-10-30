"""Flat facade for hardware layer (localized).

Primary entry point for hardware factories and common components.
"""

# Factory helpers
from .factory import create_hardware_factory, detect_hardware_platform, log_hardware_summary

# Explicitly re-export common factories and components
from .mock.mock_factory import MockHardwareFactory
from .gpio.gpio_factory import GPIOHardwareFactory
from .webui.webui_factory import WebUIHardwareFactory

# Frequently used concrete components for scripts/tests
from .gpio.gpio_hardware import GPIODisplay
from .gpio.gpio_screens import GPIORichScreen

# Mock component re-exports for tests and development
from .mock.mock_hardware import (
    MockButtons,
    MockGoButton,
    MockLeds,
    MockSwitches,
    MockDisplay,
    MockScreen,
    MockSpeaker,
)

__all__ = [
    # factory helpers
    "create_hardware_factory",
    "detect_hardware_platform",
    "log_hardware_summary",
    # factories
    "MockHardwareFactory",
    "GPIOHardwareFactory",
    "WebUIHardwareFactory",
    # concrete components
    "GPIODisplay",
    "GPIORichScreen",
    # mock components
    "MockButtons",
    "MockGoButton",
    "MockLeds",
    "MockSwitches",
    "MockDisplay",
    "MockScreen",
    "MockSpeaker",
]
