"""
WebUI hardware factory implementation.
"""

import logging
from typing import Optional
from boss.domain.interfaces.hardware import HardwareFactory, ButtonInterface, GoButtonInterface, LedInterface, SwitchInterface, DisplayInterface, ScreenInterface, SpeakerInterface
from boss.domain.models.config import HardwareConfig
from .webui_hardware import WebUIButtons, WebUIGoButton, WebUILeds, WebUISwitches, WebUIDisplay, WebUIScreen, WebUISpeaker

logger = logging.getLogger(__name__)


class WebUIHardwareFactory(HardwareFactory):
    """Factory for creating WebUI hardware implementations."""
    
    def __init__(self, hardware_config: HardwareConfig):
        self.hardware_config = hardware_config
        logger.info("WebUI hardware factory initialized")
    
    def create_buttons(self) -> ButtonInterface:
        """Create WebUI button interface implementation."""
        return WebUIButtons()
    
    def create_go_button(self) -> GoButtonInterface:
        """Create WebUI Go button interface implementation."""
        return WebUIGoButton()
    
    def create_leds(self) -> LedInterface:
        """Create WebUI LED interface implementation."""
        return WebUILeds()
    
    def create_switches(self) -> SwitchInterface:
        """Create WebUI switch interface implementation."""
        return WebUISwitches()
    
    def create_display(self) -> DisplayInterface:
        """Create WebUI display interface implementation."""
        return WebUIDisplay()
    
    def create_screen(self) -> ScreenInterface:
        """Create WebUI screen interface implementation."""
        return WebUIScreen(
            width=self.hardware_config.screen_width,
            height=self.hardware_config.screen_height
        )
    
    def create_speaker(self) -> Optional[SpeakerInterface]:
        """Create WebUI speaker interface implementation."""
        if self.hardware_config.enable_audio:
            return WebUISpeaker()
        return None
    
    @property
    def hardware_type(self) -> str:
        """Get the type of hardware implementation (gpio, webui, mock)."""
        return "webui"
