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
        self._current_screen_backend = 'textual'
        logger.info("Mock hardware factory initialized (logical textual backend)")
    
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

    # --- Backend helpers (simplified single textual path) ---
    def get_current_screen_backend(self) -> str:
        return self._current_screen_backend

    def switch_screen_backend(self, backend_type: str) -> bool:
        logger.info("Runtime backend switching disabled (single textual backend)")
        return False
    
    def create_speaker(self) -> Optional[SpeakerInterface]:
        """Create mock speaker interface implementation."""
        if self.hardware_config.enable_audio:
            return MockSpeaker()
        return None
    
    @property
    def hardware_type(self) -> str:
        """Get the type of hardware implementation (gpio, webui, mock)."""
        return "mock"

    # Optional hooks: no-ops for Mock
    def attach_event_bus(self, event_bus, components=None) -> None:
        return None

    def start_dev_ui(self, event_bus, components=None) -> Optional[int]:
        return None

    def stop_dev_ui(self) -> None:
        return None
