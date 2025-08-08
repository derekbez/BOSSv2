"""
GPIO hardware implementations for Raspberry Pi.
"""

import logging
import threading
import time
from typing import Optional, Callable, Dict

logger = logging.getLogger(__name__)

try:
    from gpiozero import Device, Button as GZButton, LED as GZLED
    # Explicitly set pin factory to lgpio for optimal performance and to eliminate warnings
    try:
        from gpiozero.pins.lgpio import LGPIOFactory
        Device.pin_factory = LGPIOFactory()
        logger.info("Using lgpio pin factory for gpiozero (optimal)")
    except ImportError:
        # Fallback to default factory selection if lgpio not available
        logger.info("lgpio not available, using gpiozero default pin factory")
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False


from boss.domain.interfaces.hardware import (
    ButtonInterface, GoButtonInterface, LedInterface, SwitchInterface, 
    DisplayInterface, ScreenInterface, SpeakerInterface
)
from boss.domain.models.hardware_state import LedColor, ButtonColor, LedState, SwitchState
from boss.domain.models.config import HardwareConfig


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
        """Initialize GPIO buttons using gpiozero."""
        if not HAS_GPIO:
            logger.error("gpiozero not available")
            return False
        try:
            self._gz_buttons = {}
            for color, pin in self.hardware_config.button_pins.items():
                btn = GZButton(pin, pull_up=True, bounce_time=0.05)
                btn.when_pressed = lambda c=color: self._handle_press(c)
                btn.when_released = lambda c=color: self._handle_release(c)
                self._gz_buttons[color] = btn
            self._available = True
            logger.info("GPIO buttons initialized (gpiozero)")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize GPIO buttons (gpiozero): {e}")
            return False

    def _handle_press(self, color):
        self._button_states[color] = True
        callback = self._press_callbacks.get(color)
        if callback:
            callback(color)
        logger.debug(f"GPIO button {color} pressed")

    def _handle_release(self, color):
        self._button_states[color] = False
        callback = self._release_callbacks.get(color)
        if callback:
            callback(color)
        logger.debug(f"GPIO button {color} released")
    
    def cleanup(self) -> None:
        """Clean up GPIO buttons."""
        if HAS_GPIO and self._available:
            try:
                for btn in getattr(self, '_gz_buttons', {}).values():
                    btn.close()
                self._gz_buttons = {}
                self._available = False
                logger.debug("GPIO buttons cleaned up (gpiozero)")
            except Exception as e:
                logger.error(f"Error cleaning up GPIO buttons: {e}")
    
    @property
    def is_available(self) -> bool:
        return self._available and HAS_GPIO
    
    def is_pressed(self, color: ButtonColor) -> bool:
        """Check if a button is currently pressed."""
        if not self.is_available:
            return False
        btn = getattr(self, '_gz_buttons', {}).get(color)
        if btn is None:
            return False
        return btn.is_pressed
    
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
        """Initialize GPIO Go button using gpiozero."""
        if not HAS_GPIO:
            logger.error("gpiozero not available")
            return False
        try:
            from gpiozero import Button as GZButton
            self._gz_button = GZButton(self.hardware_config.go_button_pin, pull_up=True, bounce_time=0.2)
            self._gz_button.when_pressed = self._handle_press
            self._available = True
            logger.info("GPIO Go button initialized (gpiozero)")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize GPIO Go button (gpiozero): {e}")
            return False

    def _handle_press(self):
        self._pressed = True
        if self._press_callback:
            self._press_callback()
        logger.debug("GPIO Go button pressed")
    
    def cleanup(self) -> None:
        """Clean up GPIO Go button."""
        if HAS_GPIO and self._available:
            try:
                if hasattr(self, '_gz_button'):
                    self._gz_button.close()
                self._available = False
                logger.debug("GPIO Go button cleaned up (gpiozero)")
            except Exception as e:
                logger.error(f"Error cleaning up GPIO Go button: {e}")
    
    @property
    def is_available(self) -> bool:
        return self._available and HAS_GPIO
    
    def is_pressed(self) -> bool:
        """Check if the Go button is currently pressed."""
        if not self.is_available:
            return False
        btn = getattr(self, '_gz_button', None)
        if btn is None:
            return False
        return btn.is_pressed
    
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
        """Initialize GPIO LEDs using gpiozero."""
        if not HAS_GPIO:
            logger.error("gpiozero not available")
            return False
        try:
            self._gz_leds = {}
            for color, pin in self.hardware_config.led_pins.items():
                led = GZLED(pin)
                self._gz_leds[LedColor(color)] = led
            self._available = True
            logger.info("GPIO LEDs initialized (gpiozero)")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize GPIO LEDs (gpiozero): {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up GPIO LEDs."""
        if HAS_GPIO and self._available:
            try:
                for led in getattr(self, '_gz_leds', {}).values():
                    led.close()
                self._gz_leds = {}
                self._available = False
                logger.debug("GPIO LEDs cleaned up (gpiozero)")
            except Exception as e:
                logger.error(f"Error cleaning up GPIO LEDs: {e}")
    
    @property
    def is_available(self) -> bool:
        return self._available and HAS_GPIO
    
    def set_led(self, color: LedColor, is_on: bool, brightness: float = 1.0) -> None:
        """Set LED state."""
        if not self.is_available:
            return
        led = getattr(self, '_gz_leds', {}).get(color)
        if led is None:
            logger.error(f"No gpiozero LED object for color: {color}")
            return
        try:
            if is_on:
                led.value = brightness
            else:
                led.off()
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
        """Initialize GPIO switches using gpiozero."""
        if not HAS_GPIO:
            logger.error("gpiozero not available")
            return False
        try:
            from gpiozero import DigitalInputDevice, DigitalOutputDevice
            self._data_pin = DigitalInputDevice(self.hardware_config.switch_data_pin, pull_up=True)
            self._select_pins = [DigitalOutputDevice(pin) for pin in self.hardware_config.switch_select_pins]
            self._available = True
            self._start_monitoring()
            logger.info("GPIO switches initialized (gpiozero)")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize GPIO switches (gpiozero): {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up GPIO switches."""
        if self._available:
            self._stop_monitoring()
            try:
                if hasattr(self, '_data_pin'):
                    self._data_pin.close()
                if hasattr(self, '_select_pins'):
                    for pin in self._select_pins:
                        pin.close()
            except Exception as e:
                logger.error(f"Error cleaning up GPIO switches: {e}")
            self._available = False
            logger.debug("GPIO switches cleaned up (gpiozero)")
    
    @property
    def is_available(self) -> bool:
        return self._available and HAS_GPIO
    
    def read_switches(self) -> SwitchState:
        """Read current switch state using gpiozero."""
        if not self.is_available:
            return SwitchState(value=0, individual_switches={i: False for i in range(8)})
        try:
            switch_value = 0
            individual_switches = {}
            for i in range(8):
                # Set select pins for current switch
                for j, pin in enumerate(self._select_pins):
                    pin.value = (i >> j) & 1
                time.sleep(0.001)
                # Read switch state (active low)
                switch_on = not self._data_pin.value
                individual_switches[i] = switch_on
                if switch_on:
                    switch_value |= (1 << i)
            self._switch_value = switch_value
            self._individual_switches = individual_switches
            return SwitchState(value=switch_value, individual_switches=individual_switches)
        except Exception as e:
            logger.error(f"Error reading GPIO switches (gpiozero): {e}")
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


class GPIODisplay(DisplayInterface):
    """GPIO 7-segment display implementation (placeholder)."""
    def __init__(self, hardware_config: HardwareConfig):
        self.hardware_config = hardware_config
        self._available = False
        self._last_value = None

    def initialize(self) -> bool:
        # TODO: Implement with python-tm1637
        logger.warning("GPIODisplay not fully implemented - using placeholder")
        self._available = True
        return True

    def cleanup(self) -> None:
        self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    def show_number(self, value: int, brightness: float = 1.0) -> None:
        self._last_value = value
        logger.info(f"GPIODisplay show_number: {value} (brightness {brightness})")

    def show_text(self, text: str, brightness: float = 1.0) -> None:
        self._last_value = text
        logger.info(f"GPIODisplay show_text: {text} (brightness {brightness})")

    def clear(self) -> None:
        self._last_value = None
        logger.info("GPIODisplay cleared")

    def set_brightness(self, brightness: float) -> None:
        logger.info(f"GPIODisplay brightness: {brightness}")


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
