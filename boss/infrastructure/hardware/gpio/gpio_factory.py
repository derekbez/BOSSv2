"""
GPIO hardware factory implementation.
"""

import logging
import os
import sys
from typing import Optional
from boss.domain.interfaces.hardware import HardwareFactory, ButtonInterface, GoButtonInterface, LedInterface, SwitchInterface, DisplayInterface, ScreenInterface, SpeakerInterface
from boss.domain.models.config import HardwareConfig
from .gpio_hardware import GPIOButtons, GPIOGoButton, GPIOLeds, GPIOSwitches, GPIODisplay, GPIOSpeaker
from .gpio_screens import GPIOPillowScreen, GPIORichScreen
try:
    from .textual_screen import TextualScreen  # type: ignore
    HAS_TEXTUAL = True
except Exception:  # pragma: no cover
    TextualScreen = None  # type: ignore
    HAS_TEXTUAL = False

logger = logging.getLogger(__name__)


class GPIOHardwareFactory(HardwareFactory):
    """Factory for creating GPIO hardware implementations."""
    
    def __init__(self, hardware_config: HardwareConfig):
        self.hardware_config = hardware_config
        # Track current screen backend for runtime switching
        self._current_screen_backend = getattr(self.hardware_config, 'screen_backend', 'rich')
        self._screen_instance: Optional[ScreenInterface] = None
        logger.info("GPIO hardware factory initialized")
    
    def create_buttons(self) -> ButtonInterface:
        """Create GPIO button interface implementation."""
        return GPIOButtons(self.hardware_config)
    
    def create_go_button(self) -> GoButtonInterface:
        """Create GPIO Go button interface implementation."""
        return GPIOGoButton(self.hardware_config)
    
    def create_leds(self) -> LedInterface:
        """Create GPIO LED interface implementation."""
        return GPIOLeds(self.hardware_config)
    
    def create_switches(self) -> SwitchInterface:
        """Create GPIO switch interface implementation."""
        return GPIOSwitches(self.hardware_config)
    
    def create_display(self) -> DisplayInterface:
        """Create GPIO display interface implementation."""
        return GPIODisplay(self.hardware_config)
    
    def create_screen(self) -> ScreenInterface:
        """Create screen implementation (textual|rich|pillow[deprecated]|auto).

        Deprecation policy:
          - 'pillow' remains selectable explicitly for legacy framebuffer/image use
          - Auto mode will NOT choose pillow anymore; it prefers textual (TTY/headless) then rich
        """
        requested = (self._current_screen_backend or getattr(self.hardware_config, 'screen_backend', 'rich')).lower()
        backend = self._resolve_backend(requested)
        self._screen_instance = self._instantiate_backend(backend)
        self._current_screen_backend = backend
        return self._screen_instance

    # --- internal helpers ---
    def _resolve_backend(self, requested: str) -> str:
        """Determine effective backend after env overrides & auto logic."""
        # Env override to disable textual (US-TXT-13)
        if os.getenv('BOSS_DISABLE_TEXTUAL') == '1' and requested == 'textual':
            logger.info("BOSS_DISABLE_TEXTUAL=1 set; overriding textual -> rich")
            return 'rich'
        if requested == 'auto':
            try:  # prefer textual when headless TTY and textual present
                if os.name == 'posix' and sys.stdout.isatty() and not os.getenv('DISPLAY') and HAS_TEXTUAL:
                    logger.info("Auto screen backend selected: textual")
                    return 'textual'
                logger.info("Auto screen backend selected: rich")
                return 'rich'
            except Exception as e:  # pragma: no cover
                logger.debug(f"Auto backend selection error: {e}; falling back to rich")
                return 'rich'
        return requested

    def _instantiate_backend(self, backend: str) -> ScreenInterface:
        """Instantiate chosen backend (with fallbacks & warnings)."""
        if backend == 'textual':
            if HAS_TEXTUAL and TextualScreen is not None:  # type: ignore
                return TextualScreen(self.hardware_config)  # type: ignore
            logger.warning("Textual backend requested but unavailable; falling back to rich")
            return GPIORichScreen(self.hardware_config)
        if backend == 'rich':
            return GPIORichScreen(self.hardware_config)
        if backend == 'pillow':
            logger.warning("Pillow backend DEPRECATED; consider 'textual' or 'rich'.")
            return GPIOPillowScreen(self.hardware_config)
        logger.warning(f"Unknown backend '{backend}' requested; defaulting to rich")
        return GPIORichScreen(self.hardware_config)

    # --- US-027 helpers ---
    def get_current_screen_backend(self) -> str:
        return self._current_screen_backend

    def switch_screen_backend(self, backend_type: str) -> bool:
        backend = (backend_type or '').lower()
        if backend not in {"rich", "textual", "auto"}:
            logger.warning(f"Invalid backend '{backend_type}', keeping current: {self._current_screen_backend}")
            return False
        try:
            if self._screen_instance is not None:
                try:
                    self._screen_instance.cleanup()
                except Exception as e:
                    logger.warning(f"Error cleaning up current screen: {e}")
            self._current_screen_backend = backend
            # Recreate screen; initialization handled by HardwareManager
            self._screen_instance = None
            logger.info(f"GPIO screen backend set to: {backend}")
            return True
        except Exception as e:
            logger.error(f"Failed to switch GPIO screen backend to {backend}: {e}")
            return False
    
    def create_speaker(self) -> Optional[SpeakerInterface]:
        """Create GPIO speaker interface implementation."""
        if self.hardware_config.enable_audio:
            return GPIOSpeaker(self.hardware_config)
        return None
    
    @property
    def hardware_type(self) -> str:
        """Get the type of hardware implementation (gpio, webui, mock)."""
        return "gpio"

    # Optional hooks: no-ops for GPIO
    def attach_event_bus(self, event_bus, components=None) -> None:
        return None

    def start_dev_ui(self, event_bus, components=None) -> Optional[int]:
        return None

    def stop_dev_ui(self) -> None:
        return None
