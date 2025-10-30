"""
GPIO hardware factory implementation.
"""

import logging
import os
import sys
from typing import Optional
from boss.core.interfaces.hardware import HardwareFactory, ButtonInterface, GoButtonInterface, LedInterface, SwitchInterface, DisplayInterface, ScreenInterface, SpeakerInterface
from boss.core.models import HardwareConfig
from .gpio_hardware import GPIOButtons, GPIOGoButton, GPIOLeds, GPIOSwitches, GPIODisplay, GPIOSpeaker
from .gpio_screens import GPIORichScreen  # Rich kept as internal fallback only (no direct selection)
try:
    from .textual_screen import TextualScreen  # type: ignore
    HAS_TEXTUAL = True
except Exception:  # pragma: no cover
    TextualScreen = None  # type: ignore
    HAS_TEXTUAL = False

logger = logging.getLogger(__name__)


class GPIOHardwareFactory(HardwareFactory):
    """Factory for creating GPIO hardware implementations (textual-only screen backend)."""

    def __init__(self, hardware_config: HardwareConfig):
        self.hardware_config = hardware_config
        self._current_screen_backend = 'textual'
        self._screen_instance: Optional[ScreenInterface] = None
        logger.info("GPIO hardware factory initialized (textual backend)")

    # --- Component creators ---
    def create_buttons(self) -> ButtonInterface:
        return GPIOButtons(self.hardware_config)

    def create_go_button(self) -> GoButtonInterface:
        return GPIOGoButton(self.hardware_config)

    def create_leds(self) -> LedInterface:
        return GPIOLeds(self.hardware_config)

    def create_switches(self) -> SwitchInterface:
        return GPIOSwitches(self.hardware_config)

    def create_display(self) -> DisplayInterface:
        return GPIODisplay(self.hardware_config)

    def create_screen(self) -> ScreenInterface:
        """Create the (textual) screen instance with Rich fallback only if Textual unavailable."""
        if self._screen_instance is not None:
            return self._screen_instance
        if HAS_TEXTUAL and TextualScreen is not None:  # type: ignore
            self._screen_instance = TextualScreen(self.hardware_config)  # type: ignore
        else:  # pragma: no cover - rare fallback
            logger.warning("Textual backend unavailable; using minimal Rich screen fallback")
            self._screen_instance = GPIORichScreen(self.hardware_config)
        return self._screen_instance

    # --- Backend helpers (API surface retained for compatibility) ---
    def get_current_screen_backend(self) -> str:
        return self._current_screen_backend

    def switch_screen_backend(self, backend_type: str) -> bool:  # pragma: no cover - disabled path
        logger.info("Runtime backend switching disabled (single textual backend)")
        return False

    def create_speaker(self) -> Optional[SpeakerInterface]:
        if getattr(self.hardware_config, 'enable_audio', False):
            return GPIOSpeaker(self.hardware_config)
        return None

    @property
    def hardware_type(self) -> str:
        return "gpio"

    # Optional hooks (no-ops for GPIO implementation)
    def attach_event_bus(self, event_bus, components=None) -> None:
        return None

    def start_dev_ui(self, event_bus, components=None) -> Optional[int]:
        return None

    def stop_dev_ui(self) -> None:
        return None
