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
        self._current_screen_backend = getattr(self.hardware_config, 'screen_backend', 'rich')
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

    # --- US-027 helpers (track backend; UI rendering is the same) ---
    def get_current_screen_backend(self) -> str:
        return self._current_screen_backend

    def switch_screen_backend(self, backend_type: str) -> bool:
        backend = (backend_type or '').lower()
        if backend not in {"rich", "textual", "auto"}:
            logger.warning(f"Invalid backend '{backend_type}', keeping current: {self._current_screen_backend}")
            return False
        # WebUI always renders via browser; we just record logical preference
        self._current_screen_backend = backend
        logger.info(f"WebUI logical screen backend set to: {backend}")
        return True
    
    def create_speaker(self) -> Optional[SpeakerInterface]:
        """Create WebUI speaker interface implementation."""
        if self.hardware_config.enable_audio:
            return WebUISpeaker()
        return None
    
    @property
    def hardware_type(self) -> str:
        """Get the type of hardware implementation (gpio, webui, mock)."""
        return "webui"

    # --- Optional hooks to keep services agnostic ---
    def attach_event_bus(self, event_bus, components: Optional[dict] = None) -> None:
        try:
            comps = components or {}
            for key in ("display", "screen", "leds"):
                comp = comps.get(key)
                if comp and hasattr(comp, "set_event_bus"):
                    comp.set_event_bus(event_bus)  # type: ignore
        except Exception as e:
            logger.debug(f"WebUI attach_event_bus ignored: {e}")

    def start_dev_ui(self, event_bus, components: Optional[dict] = None) -> Optional[int]:
        try:
            from boss.presentation.api.web_ui_main import start_web_ui
            return start_web_ui(components or {}, event_bus)
        except Exception as e:
            logger.warning(f"Could not start WebUI development interface: {e}")
            return None

    def stop_dev_ui(self) -> None:
        try:
            from boss.presentation.api.web_ui_main import stop_web_ui
            stop_web_ui()
        except Exception as e:
            logger.debug(f"Error stopping WebUI: {e}")
