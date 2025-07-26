"""
Hardware Service - Coordinates all hardware components and monitoring.
"""

import logging
import threading
import time
from typing import Optional
from boss.domain.models.hardware_state import HardwareState, SwitchState
from boss.domain.interfaces.services import HardwareService
from boss.domain.interfaces.hardware import HardwareFactory

logger = logging.getLogger(__name__)


class HardwareManager(HardwareService):
    """Service for coordinating all hardware components."""
    
    def __init__(self, hardware_factory: HardwareFactory, event_bus):
        self.hardware_factory = hardware_factory
        self.event_bus = event_bus
        
        # Hardware components
        self.buttons = None
        self.go_button = None
        self.leds = None
        self.switches = None
        self.display = None
        self.screen = None
        self.speaker = None
        
        # Monitoring
        self._monitoring_thread: Optional[threading.Thread] = None
        self._monitoring_active = False
        self._last_switch_value = 0
        
        # State
        self._hardware_state = HardwareState.create_default()
    
    def initialize(self) -> None:
        """Initialize all hardware components."""
        logger.info(f"Initializing {self.hardware_factory.hardware_type} hardware")
        
        try:
            # Create hardware components
            self.buttons = self.hardware_factory.create_buttons()
            self.go_button = self.hardware_factory.create_go_button()
            self.leds = self.hardware_factory.create_leds()
            self.switches = self.hardware_factory.create_switches()
            self.display = self.hardware_factory.create_display()
            self.screen = self.hardware_factory.create_screen()
            self.speaker = self.hardware_factory.create_speaker()  # May be None
            
            # Initialize each component
            components = [
                ("Buttons", self.buttons),
                ("Go Button", self.go_button),
                ("LEDs", self.leds),
                ("Switches", self.switches),
                ("Display", self.display),
                ("Screen", self.screen),
            ]
            
            if self.speaker:
                components.append(("Speaker", self.speaker))
            
            for name, component in components:
                if component and component.initialize():
                    logger.info(f"[OK] {name} initialized")
                else:
                    logger.warning(f"✗ {name} failed to initialize")
            
            # Set up hardware callbacks
            self._setup_callbacks()
            
            # For WebUI hardware, set the event bus
            self._setup_webui_event_bus()
            
            # Subscribe to app API events
            self._setup_event_subscriptions()
            
            # Update initial state
            self._update_hardware_state()
            
            logger.info("Hardware initialization complete")
            
        except Exception as e:
            logger.error(f"Hardware initialization failed: {e}")
            raise
    
    def cleanup(self) -> None:
        """Clean up all hardware resources."""
        logger.info("Cleaning up hardware")
        
        # Stop monitoring
        self.stop_monitoring()
        
        # Clean up components
        components = [self.buttons, self.go_button, self.leds, self.switches, 
                     self.display, self.screen, self.speaker]
        
        for component in components:
            if component:
                try:
                    component.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up hardware component: {e}")
        
        logger.info("Hardware cleanup complete")
    
    def get_hardware_state(self) -> HardwareState:
        """Get current state of all hardware."""
        self._update_hardware_state()
        return self._hardware_state
    
    def start_monitoring(self) -> None:
        """Start monitoring hardware for changes."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(
            target=self._monitor_hardware,
            daemon=True,
            name="HardwareMonitor"
        )
        self._monitoring_thread.start()
        logger.info("Hardware monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop monitoring hardware."""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=2.0)
        
        logger.info("Hardware monitoring stopped")

    def _setup_webui_event_bus(self) -> None:
        """Set up event bus for WebUI hardware components."""
        # Check if we're using WebUI hardware and set event bus
        if self.display and hasattr(self.display, 'set_event_bus'):
            self.display.set_event_bus(self.event_bus)  # type: ignore
            logger.debug("Event bus set for WebUI display")
        
        if self.screen and hasattr(self.screen, 'set_event_bus'):
            self.screen.set_event_bus(self.event_bus)  # type: ignore
            logger.debug("Event bus set for WebUI screen")
        
        if self.leds and hasattr(self.leds, 'set_event_bus'):
            self.leds.set_event_bus(self.event_bus)  # type: ignore
            logger.debug("Event bus set for WebUI LEDs")

    def _setup_event_subscriptions(self) -> None:
        """Subscribe to app API events."""
        # Note: Hardware events are now handled by HardwareEventHandler, not directly here
        # Subscribe only to display events from apps (not screen events)
        self.event_bus.subscribe("display_update", self._on_display_update)
        logger.debug("Subscribed to app API events")
    
    def _on_display_update(self, event_type: str, payload: dict, source: Optional[str] = None) -> None:
        """Handle display update events from apps."""
        if not self.display:
            return
            
        if "value" in payload:
            value = payload["value"]
            if isinstance(value, int) and 0 <= value <= 9999:
                self.display.show_number(value)
                logger.debug(f"Display updated with number from {source}: {value}")
        elif "text" in payload:
            text = payload["text"]
            self.display.show_text(text)
            logger.debug(f"Display updated with text from {source}: '{text}'")

    def _setup_callbacks(self) -> None:
        """Set up hardware event callbacks."""
        try:
            # Go button callback
            if self.go_button:
                self.go_button.set_press_callback(self._on_go_button_pressed)
            
            # Color button callbacks
            if self.buttons:
                from boss.domain.models.hardware_state import ButtonColor
                for color in ButtonColor:
                    self.buttons.set_press_callback(color, 
                        lambda c=color: self._on_button_pressed(c.value))
                    self.buttons.set_release_callback(color,
                        lambda c=color: self._on_button_released(c.value))
            
            # Switch change callback
            if self.switches:
                self.switches.set_change_callback(self._on_switch_changed)
            
        except Exception as e:
            logger.error(f"Error setting up hardware callbacks: {e}")
    
    def _on_go_button_pressed(self) -> None:
        """Handle Go button press."""
        logger.debug("Go button pressed")
        self.event_bus.publish("go_button_pressed", {}, "hardware")
    
    def _on_button_pressed(self, color: str) -> None:
        """Handle color button press."""
        logger.debug(f"{color} button pressed")
        self.event_bus.publish("button_pressed", {"button": color}, "hardware")
    
    def _on_button_released(self, color: str) -> None:
        """Handle color button release."""
        logger.debug(f"{color} button released")
        self.event_bus.publish("button_released", {"button": color}, "hardware")
    
    def _on_switch_changed(self, old_value: int, new_value: int) -> None:
        """Handle switch change."""
        logger.debug(f"Switches changed: {old_value} -> {new_value}")
        self.event_bus.publish("switch_changed", {
            "old_value": old_value,
            "new_value": new_value
        }, "hardware")
        self._last_switch_value = new_value
    
    def _monitor_hardware(self) -> None:
        """Monitor hardware in background thread."""
        logger.info("Hardware monitoring thread started")
        
        while self._monitoring_active:
            try:
                # Check switches for changes
                if self.switches:
                    switch_state = self.switches.read_switches()
                    if switch_state.value != self._last_switch_value:
                        self._on_switch_changed(self._last_switch_value, switch_state.value)
                
                # Update hardware state
                self._update_hardware_state()
                
                # Sleep briefly
                time.sleep(0.1)  # 10Hz monitoring
                
            except Exception as e:
                logger.error(f"Error in hardware monitoring: {e}")
                time.sleep(1.0)  # Wait longer on error
        
        logger.info("Hardware monitoring thread stopped")
    
    def _update_hardware_state(self) -> None:
        """Update internal hardware state."""
        try:
            # Read switch state
            if self.switches:
                self._hardware_state.switches = self.switches.read_switches()
            
            # Read button states
            if self.buttons:
                from boss.domain.models.hardware_state import ButtonColor, ButtonState
                for color in ButtonColor:
                    is_pressed = self.buttons.is_pressed(color)
                    self._hardware_state.buttons[color] = ButtonState(
                        color=color,
                        is_pressed=is_pressed,
                        last_press_time=time.time() if is_pressed else None
                    )
            
            # Read Go button state
            if self.go_button:
                self._hardware_state.go_button_pressed = self.go_button.is_pressed()
            
            # LED states are managed by events, so we don't read them here
            
        except Exception as e:
            logger.error(f"Error updating hardware state: {e}")
    
    def update_led(self, color: str, is_on: bool, brightness: float = 1.0) -> None:
        """Update LED state."""
        try:
            if self.leds:
                from boss.domain.models.hardware_state import LedColor
                led_color = LedColor(color)
                self.leds.set_led(led_color, is_on, brightness)
                logger.debug(f"LED {color} {'on' if is_on else 'off'}")
        except Exception as e:
            logger.error(f"Error updating LED {color}: {e}")
    
    def update_display(self, value: Optional[int], brightness: float = 1.0) -> None:
        """Update 7-segment display."""
        try:
            if self.display:
                if value is not None:
                    self.display.show_number(value, brightness)
                else:
                    self.display.clear()
                logger.debug(f"Display updated: {value}")
        except Exception as e:
            logger.error(f"Error updating display: {e}")
    
    def update_screen(self, content_type: str, content, **kwargs) -> None:
        """Update main screen."""
        try:
            if self.screen:
                if content_type == "text":
                    self.screen.display_text(content, **kwargs)
                elif content_type == "image":
                    self.screen.display_image(content, **kwargs)
                elif content_type == "clear":
                    self.screen.clear_screen(content)
                logger.debug(f"Screen updated: {content_type}")
        except Exception as e:
            logger.error(f"Error updating screen: {e}")
