"""
GPIO hardware factory implementation.
"""

import logging
from typing import Optional
from boss.domain.interfaces.hardware import HardwareFactory, ButtonInterface, GoButtonInterface, LedInterface, SwitchInterface, DisplayInterface, ScreenInterface, SpeakerInterface
from boss.domain.models.config import HardwareConfig
from .gpio_hardware import GPIOButtons, GPIOGoButton, GPIOLeds, GPIOSwitches, GPIODisplay, GPIOScreen, GPIOSpeaker

logger = logging.getLogger(__name__)


class GPIOHardwareFactory(HardwareFactory):
    """Factory for creating GPIO hardware implementations."""
    
    def __init__(self, hardware_config: HardwareConfig):
        self.hardware_config = hardware_config
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
        """Create GPIO screen interface implementation."""
        return GPIOScreen(self.hardware_config)
    
    def create_speaker(self) -> Optional[SpeakerInterface]:
        """Create GPIO speaker interface implementation."""
        if self.hardware_config.enable_audio:
            return GPIOSpeaker(self.hardware_config)
        return None
    
    @property
    def hardware_type(self) -> str:
        """Get the type of hardware implementation (gpio, webui, mock)."""
        return "gpio"
