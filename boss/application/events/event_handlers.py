"""
Event handlers for system-level events.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SystemEventHandler:
    """Handles system-level events like startup, shutdown, errors."""
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self._setup_subscriptions()
    
    def _setup_subscriptions(self):
        """Set up event subscriptions."""
        self.event_bus.subscribe("system_started", self.on_system_started)
        self.event_bus.subscribe("system_shutdown", self.on_system_shutdown)
        self.event_bus.subscribe("app_error", self.on_app_error)
        self.event_bus.subscribe("switch_changed", self.on_switch_changed)
        self.event_bus.subscribe("go_button_pressed", self.on_go_button_pressed)
    
    def on_system_started(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Handle system startup."""
        hardware_type = payload.get("hardware_type", "unknown")
        logger.info(f"BOSS system started with {hardware_type} hardware")
    
    def on_system_shutdown(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Handle system shutdown."""
        reason = payload.get("reason", "unknown")
        logger.info(f"BOSS system shutting down: {reason}")
    
    def on_app_error(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Handle app errors."""
        app_name = payload.get("app_name", "unknown")
        error = payload.get("error", "unknown error")
        logger.error(f"App error in {app_name}: {error}")
    
    def on_switch_changed(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Handle switch changes."""
        old_value = payload.get("old_value", 0)
        new_value = payload.get("new_value", 0)
        logger.info(f"Switch changed from {old_value} to {new_value}")
        
        # Publish display update event
        self.event_bus.publish("display_update", {"value": new_value}, "system")
    
    def on_go_button_pressed(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Handle Go button presses."""
    logger.info("Go button pressed")
    # App launch orchestration is handled by SystemManager subscriber


class HardwareEventHandler:
    """Handles hardware output events (LEDs, display, screen)."""
    
    def __init__(self, event_bus, hardware_service):
        self.event_bus = event_bus
        self.hardware_service = hardware_service
        self._setup_subscriptions()
    
    def _setup_subscriptions(self):
        """Set up event subscriptions."""
        self.event_bus.subscribe("led_update", self.on_led_update)
        self.event_bus.subscribe("display_update", self.on_display_update)
        self.event_bus.subscribe("screen_update", self.on_screen_update)
    
    def on_led_update(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Handle LED update requests."""
        try:
            color = payload.get("color")
            is_on = payload.get("is_on", False)
            brightness = payload.get("brightness", 1.0)
            
            # Update hardware via service
            self.hardware_service.update_led(color, is_on, brightness)
            logger.debug(f"LED update processed: {color} {'on' if is_on else 'off'} at {brightness}")
            
        except Exception as e:
            logger.error(f"Error updating LED: {e}")
    
    def on_display_update(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Handle 7-segment display update requests."""
        try:
            value = payload.get("value")
            brightness = payload.get("brightness", 1.0)
            
            # Only allow system-driven numeric updates (e.g., switch mirror).
            # Ignore None clears and any updates not originating from system layer.
            if value is None:
                logger.debug("Ignoring display clear request; 7-seg is system-controlled.")
                return
            
            # Update hardware via service
            self.hardware_service.update_display(value, brightness)
            logger.debug(f"Display update processed: {value} at brightness {brightness}")
            
        except Exception as e:
            logger.error(f"Error updating display: {e}")
    
    def on_screen_update(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Handle screen update requests."""
        try:
            content_type = payload.get("content_type", "text")
            content = payload.get("content", "")
            
            # Update hardware via service using the unified update_screen method
            if content_type == "text":
                self.hardware_service.update_screen(
                    content_type=content_type,
                    content=content,
                    font_size=payload.get("font_size", 24),
                    color=payload.get("color", "white"),
                    background=payload.get("background", "black"),
                    align=payload.get("align", "center")
                )
            elif content_type == "image":
                self.hardware_service.update_screen(
                    content_type=content_type,
                    content=content,
                    scale=payload.get("scale", 1.0),
                    position=payload.get("position", (0, 0))
                )
            elif content_type == "clear":
                self.hardware_service.update_screen(
                    content_type=content_type,
                    content=content  # content is the color
                )
            
            logger.debug(f"Screen update processed: {content_type}")
            
        except Exception as e:
            logger.error(f"Error updating screen: {e}")
