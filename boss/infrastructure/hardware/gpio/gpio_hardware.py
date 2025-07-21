"""
GPIO hardware implementations for Raspberry Pi.
"""

import logging
import threading
import time
from typing import Optional, Callable, Dict

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False
    GPIO = None

from boss.domain.interfaces.hardware import (
    ButtonInterface, GoButtonInterface, LedInterface, SwitchInterface, 
    DisplayInterface, ScreenInterface, SpeakerInterface
)
from boss.domain.models.hardware_state import LedColor, ButtonColor, LedState, SwitchState
from boss.domain.models.config import HardwareConfig

logger = logging.getLogger(__name__)


class GPIOButtons(ButtonInterface):
    """GPIO button implementation for Raspberry Pi."""
    
    def __init__(self, hardware_config: HardwareConfig):
        self.hardware_config = hardware_config
        self._button_states: Dict[ButtonColor, bool] = {
            color: False for color in ButtonColor
        }
        self._press_callbacks: Dict[ButtonColor, Optional[Callable]] = {
            color: None for color in ButtonColor
        }
        self._release_callbacks: Dict[ButtonColor, Optional[Callable]] = {
            color: None for color in ButtonColor
        }
        self._available = False
    
    def initialize(self) -> bool:
        """Initialize GPIO buttons."""
        if not HAS_GPIO:
            logger.error("RPi.GPIO not available")
            return False
        
        try:
            GPIO.setmode(GPIO.BCM)
            
            # Set up button pins
            for color, pin in self.hardware_config.button_pins.items():
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                
                # Set up interrupt for button press detection
                GPIO.add_event_detect(pin, GPIO.BOTH, 
                                    callback=self._button_callback, 
                                    bouncetime=50)
            
            self._available = True
            logger.info("GPIO buttons initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize GPIO buttons: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up GPIO buttons."""
        if HAS_GPIO and self._available:
            try:
                for pin in self.hardware_config.button_pins.values():
                    GPIO.remove_event_detect(pin)
                self._available = False
                logger.debug("GPIO buttons cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up GPIO buttons: {e}")
    
    @property
    def is_available(self) -> bool:
        return self._available and HAS_GPIO
    
    def is_pressed(self, color: ButtonColor) -> bool:
        """Check if a button is currently pressed."""
        if not self.is_available:
            return False
        
        pin = self.hardware_config.button_pins.get(color.value)
        if pin is None:
            return False
        
        # Button is pressed when pin is LOW (pull-up resistor)
        return GPIO.input(pin) == GPIO.LOW
    
    def set_press_callback(self, color: ButtonColor, callback: Callable[[ButtonColor], None]) -> None:
        """Set callback for button press events."""
        self._press_callbacks[color] = callback
    
    def set_release_callback(self, color: ButtonColor, callback: Callable[[ButtonColor], None]) -> None:
        """Set callback for button release events."""
        self._release_callbacks[color] = callback
    
    def _button_callback(self, pin: int) -> None:
        """GPIO interrupt callback for button events."""
        try:
            # Find which button this pin corresponds to
            button_color = None
            for color, button_pin in self.hardware_config.button_pins.items():
                if button_pin == pin:
                    button_color = ButtonColor(color)
                    break
            
            if button_color is None:
                return
            
            # Check if button is pressed or released
            is_pressed = GPIO.input(pin) == GPIO.LOW
            old_state = self._button_states[button_color]
            self._button_states[button_color] = is_pressed
            
            # Call appropriate callback if state changed
            if is_pressed and not old_state:
                # Button pressed
                callback = self._press_callbacks.get(button_color)
                if callback:
                    callback(button_color)
                logger.debug(f"GPIO button {button_color.value} pressed")
            
            elif not is_pressed and old_state:
                # Button released
                callback = self._release_callbacks.get(button_color)
                if callback:
                    callback(button_color)
                logger.debug(f"GPIO button {button_color.value} released")
                
        except Exception as e:
            logger.error(f"Error in button callback: {e}")


class GPIOGoButton(GoButtonInterface):
    """GPIO Go button implementation."""
    
    def __init__(self, hardware_config: HardwareConfig):
        self.hardware_config = hardware_config
        self._pressed = False
        self._press_callback: Optional[Callable] = None
        self._available = False
    
    def initialize(self) -> bool:
        """Initialize GPIO Go button."""
        if not HAS_GPIO:
            logger.error("RPi.GPIO not available")
            return False
        
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.hardware_config.go_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Set up interrupt for Go button
            GPIO.add_event_detect(self.hardware_config.go_button_pin, GPIO.FALLING, 
                                callback=self._go_button_callback, 
                                bouncetime=200)
            
            self._available = True
            logger.info("GPIO Go button initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize GPIO Go button: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up GPIO Go button."""
        if HAS_GPIO and self._available:
            try:
                GPIO.remove_event_detect(self.hardware_config.go_button_pin)
                self._available = False
                logger.debug("GPIO Go button cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up GPIO Go button: {e}")
    
    @property
    def is_available(self) -> bool:
        return self._available and HAS_GPIO
    
    def is_pressed(self) -> bool:
        """Check if the Go button is currently pressed."""
        if not self.is_available:
            return False
        return GPIO.input(self.hardware_config.go_button_pin) == GPIO.LOW
    
    def set_press_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for Go button press events."""
        self._press_callback = callback
    
    def _go_button_callback(self, pin: int) -> None:
        """GPIO interrupt callback for Go button."""
        try:
            if self._press_callback:
                self._press_callback()
            logger.debug("GPIO Go button pressed")
        except Exception as e:
            logger.error(f"Error in Go button callback: {e}")


class GPIOLeds(LedInterface):
    """GPIO LED implementation."""
    
    def __init__(self, hardware_config: HardwareConfig):
        self.hardware_config = hardware_config
        self._led_states: Dict[LedColor, LedState] = {
            color: LedState(color=color, is_on=False) for color in LedColor
        }
        self._pwm_objects: Dict[LedColor, object] = {}
        self._available = False
    
    def initialize(self) -> bool:
        """Initialize GPIO LEDs."""
        if not HAS_GPIO:
            logger.error("RPi.GPIO not available")
            return False
        
        try:
            GPIO.setmode(GPIO.BCM)
            
            # Set up LED pins and PWM
            for color, pin in self.hardware_config.led_pins.items():
                GPIO.setup(pin, GPIO.OUT)
                # Create PWM instance for brightness control
                pwm = GPIO.PWM(pin, 1000)  # 1kHz frequency
                pwm.start(0)  # Start with 0% duty cycle (off)
                self._pwm_objects[LedColor(color)] = pwm
            
            self._available = True
            logger.info("GPIO LEDs initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize GPIO LEDs: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up GPIO LEDs."""
        if HAS_GPIO and self._available:
            try:
                for pwm in self._pwm_objects.values():
                    pwm.stop()
                self._pwm_objects.clear()
                self._available = False
                logger.debug("GPIO LEDs cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up GPIO LEDs: {e}")
    
    @property
    def is_available(self) -> bool:
        return self._available and HAS_GPIO
    
    def set_led(self, color: LedColor, is_on: bool, brightness: float = 1.0) -> None:
        """Set LED state."""
        if not self.is_available:
            return
        
        pwm = self._pwm_objects.get(color)
        if pwm is None:
            logger.error(f"No PWM object for LED color: {color}")
            return
        
        try:
            if is_on:
                duty_cycle = brightness * 100  # Convert to percentage
                pwm.ChangeDutyCycle(duty_cycle)
            else:
                pwm.ChangeDutyCycle(0)
            
            self._led_states[color] = LedState(color=color, is_on=is_on, brightness=brightness)
            logger.debug(f"GPIO LED {color.value}: {'ON' if is_on else 'OFF'} (brightness: {brightness})")
            
        except Exception as e:
            logger.error(f"Error setting GPIO LED {color}: {e}")
    
    def get_led_state(self, color: LedColor) -> LedState:
        """Get current LED state."""
        return self._led_states[color]
    
    def set_all_leds(self, is_on: bool, brightness: float = 1.0) -> None:
        """Set all LEDs to the same state."""
        for color in LedColor:
            self.set_led(color, is_on, brightness)


class GPIOSwitches(SwitchInterface):
    """GPIO switch implementation using shift register or multiplexer."""
    
    def __init__(self, hardware_config: HardwareConfig):
        self.hardware_config = hardware_config
        self._switch_value = 0
        self._individual_switches = {i: False for i in range(8)}
        self._change_callback: Optional[Callable] = None
        self._available = False
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
    
    def initialize(self) -> bool:
        """Initialize GPIO switches."""
        if not HAS_GPIO:
            logger.error("RPi.GPIO not available")
            return False
        
        try:
            GPIO.setmode(GPIO.BCM)
            
            # Set up pins for shift register/multiplexer
            GPIO.setup(self.hardware_config.switch_data_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.hardware_config.switch_clock_pin, GPIO.OUT)
            
            for pin in self.hardware_config.switch_select_pins:
                GPIO.setup(pin, GPIO.OUT)
            
            self._available = True
            self._start_monitoring()
            logger.info("GPIO switches initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize GPIO switches: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up GPIO switches."""
        if self._available:
            self._stop_monitoring()
            self._available = False
            logger.debug("GPIO switches cleaned up")
    
    @property
    def is_available(self) -> bool:
        return self._available and HAS_GPIO
    
    def read_switches(self) -> SwitchState:
        """Read current switch state."""
        if not self.is_available:
            return SwitchState(value=0, individual_switches={i: False for i in range(8)})
        
        try:
            # Read switches using shift register or multiplexer
            switch_value = 0
            individual_switches = {}
            
            for i in range(8):
                # Set select pins for current switch
                for j, pin in enumerate(self.hardware_config.switch_select_pins):
                    GPIO.output(pin, (i >> j) & 1)
                
                # Small delay for signal settling
                time.sleep(0.001)
                
                # Read switch state
                switch_on = GPIO.input(self.hardware_config.switch_data_pin) == GPIO.LOW
                individual_switches[i] = switch_on
                
                if switch_on:
                    switch_value |= (1 << i)
            
            self._switch_value = switch_value
            self._individual_switches = individual_switches
            
            return SwitchState(value=switch_value, individual_switches=individual_switches)
            
        except Exception as e:
            logger.error(f"Error reading GPIO switches: {e}")
            return SwitchState(value=0, individual_switches={i: False for i in range(8)})
    
    def set_change_callback(self, callback: Callable[[int, int], None]) -> None:
        """Set callback for switch change events."""
        self._change_callback = callback
    
    def _start_monitoring(self) -> None:
        """Start monitoring switches for changes."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_switches, daemon=True)
        self._monitor_thread.start()
    
    def _stop_monitoring(self) -> None:
        """Stop monitoring switches."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
    
    def _monitor_switches(self) -> None:
        """Monitor switches in background thread."""
        last_value = self._switch_value
        
        while self._monitoring:
            try:
                switch_state = self.read_switches()
                
                if switch_state.value != last_value:
                    if self._change_callback:
                        self._change_callback(last_value, switch_state.value)
                    last_value = switch_state.value
                
                time.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                logger.error(f"Error in switch monitoring: {e}")
                time.sleep(1.0)


# Note: Display, Screen, and Speaker implementations would require additional libraries
# For now, we'll use simpler implementations

class GPIODisplay(DisplayInterface):
    """GPIO 7-segment display implementation (placeholder)."""
    
    def __init__(self, hardware_config: HardwareConfig):
        self.hardware_config = hardware_config
        self._available = False
    
    def initialize(self) -> bool:
        """Initialize GPIO display."""
        # TODO: Implement with TM1637 or similar library
        logger.warning("GPIO display not fully implemented - using placeholder")
        self._available = True
        return True
    
    def cleanup(self) -> None:
        """Clean up GPIO display."""
        self._available = False
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def show_number(self, value: int, brightness: float = 1.0) -> None:
        """Display a number (0-9999)."""
        logger.info(f"GPIO display would show: {value}")
    
    def show_text(self, text: str, brightness: float = 1.0) -> None:
        """Display text (limited characters)."""
        logger.info(f"GPIO display would show text: {text}")
    
    def clear(self) -> None:
        """Clear the display."""
        logger.debug("GPIO display cleared")
    
    def set_brightness(self, brightness: float) -> None:
        """Set display brightness (0.0-1.0)."""
        logger.debug(f"GPIO display brightness: {brightness}")


class GPIOScreen(ScreenInterface):
    """GPIO screen implementation (placeholder)."""
    
    def __init__(self, hardware_config: HardwareConfig):
        self.hardware_config = hardware_config
        self._available = False
    
    def initialize(self) -> bool:
        """Initialize GPIO screen."""
        # TODO: Implement with pygame or similar
        logger.warning("GPIO screen not fully implemented - using placeholder")
        self._available = True
        return True
    
    def cleanup(self) -> None:
        """Clean up GPIO screen."""
        self._available = False
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def display_text(self, text: str, font_size: int = 24, color: str = "white", 
                    background: str = "black", align: str = "center") -> None:
        """Display text on screen."""
        logger.info(f"GPIO screen would display: '{text}'")
    
    def display_image(self, image_path: str, scale: float = 1.0, position: tuple = (0, 0)) -> None:
        """Display an image on screen."""
        logger.info(f"GPIO screen would display image: {image_path}")
    
    def clear_screen(self, color: str = "black") -> None:
        """Clear screen with specified color."""
        logger.debug(f"GPIO screen cleared with {color}")
    
    def get_screen_size(self) -> tuple:
        """Get screen dimensions (width, height)."""
        return (self.hardware_config.screen_width, self.hardware_config.screen_height)


class GPIOSpeaker(SpeakerInterface):
    """GPIO speaker implementation (placeholder)."""
    
    def __init__(self, hardware_config: HardwareConfig):
        self.hardware_config = hardware_config
        self._available = False
    
    def initialize(self) -> bool:
        """Initialize GPIO speaker."""
        # TODO: Implement with pygame mixer or similar
        logger.warning("GPIO speaker not fully implemented - using placeholder")
        self._available = True
        return True
    
    def cleanup(self) -> None:
        """Clean up GPIO speaker."""
        self._available = False
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def play_sound(self, sound_path: str, volume: float = 1.0) -> None:
        """Play a sound file."""
        logger.info(f"GPIO speaker would play: {sound_path}")
    
    def play_tone(self, frequency: int, duration: float, volume: float = 1.0) -> None:
        """Play a tone at specified frequency and duration."""
        logger.info(f"GPIO speaker would play tone: {frequency}Hz for {duration}s")
    
    def set_volume(self, volume: float) -> None:
        """Set speaker volume (0.0-1.0)."""
        logger.debug(f"GPIO speaker volume: {volume}")
