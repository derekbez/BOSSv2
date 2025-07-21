"""
Mock hardware factory implementation.
"""

import logging
from typing import Optional
from boss.domain.interfaces.hardware import HardwareFactory, ButtonInterface, GoButtonInterface, LedInterface, SwitchInterface, DisplayInterface, ScreenInterface, SpeakerInterface
from boss.domain.models.config import HardwareConfig
from .mock_hardware import MockButtons, MockGoButton, MockLeds, MockSwitches, MockDisplay, MockScreen, MockSpeaker

logger = logging.getLogger(__name__)


class MockHardwareFactory(HardwareFactory):
    """Factory for creating mock hardware implementations."""
    
    def __init__(self, hardware_config: HardwareConfig):
        self.hardware_config = hardware_config
        logger.info("Mock hardware factory initialized")
    
    def create_buttons(self) -> ButtonInterface:
        """Create mock button interface implementation."""
        return MockButtons()
    
    def create_go_button(self) -> GoButtonInterface:
        """Create mock Go button interface implementation."""
        return MockGoButton()
    
    def create_leds(self) -> LedInterface:
        """Create mock LED interface implementation."""
        return MockLeds()
    
    def create_switches(self) -> SwitchInterface:
        """Create mock switch interface implementation."""
        return MockSwitches()
    
    def create_display(self) -> DisplayInterface:
        """Create mock display interface implementation."""
        return MockDisplay()
    
    def create_screen(self) -> ScreenInterface:
        """Create mock screen interface implementation."""
        return MockScreen(
            width=self.hardware_config.screen_width,
            height=self.hardware_config.screen_height
        )
    
    def create_speaker(self) -> Optional[SpeakerInterface]:
        """Create mock speaker interface implementation."""
        if self.hardware_config.enable_audio:
            return MockSpeaker()
        return None
    
    @property
    def hardware_type(self) -> str:
        """Get the type of hardware implementation (gpio, webui, mock)."""
        return "mock"
