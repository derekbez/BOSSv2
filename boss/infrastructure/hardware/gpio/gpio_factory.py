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
        """Create screen interface implementation based on current backend (rich or pillow)."""
        backend = (self._current_screen_backend or getattr(self.hardware_config, 'screen_backend', 'rich'))
        # Heuristic: if running headless under systemd on a Pi (no TTY) and framebuffer exists, prefer Pillow
        # This ensures HDMI output works when there is no terminal attached for Rich to render to.
        try:
            if backend == 'rich' and os.path.exists('/dev/fb0') and not sys.stdout.isatty():
                logger.info("Headless + framebuffer detected; using Pillow framebuffer backend for HDMI output")
                backend = 'pillow'
        except Exception:
            pass
        if backend == 'rich':
            self._screen_instance = GPIORichScreen(self.hardware_config)
        else:
            self._screen_instance = GPIOPillowScreen(self.hardware_config)
        return self._screen_instance

    # --- US-027 helpers ---
    def get_current_screen_backend(self) -> str:
        return self._current_screen_backend

    def switch_screen_backend(self, backend_type: str) -> bool:
        backend = (backend_type or '').lower()
        if backend not in {"rich", "pillow"}:
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
