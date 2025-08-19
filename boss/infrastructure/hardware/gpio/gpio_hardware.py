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
    # Provide stubs to satisfy type checkers when gpiozero isn't available at import time
    GZButton = None  # type: ignore
    GZLED = None  # type: ignore


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
            # Import here to ensure symbols exist only when gpiozero is present
            from gpiozero import Button as GZButton  # type: ignore
            self._gz_buttons = {}
            # Normalize config keys to ButtonColor enum to avoid mismatches
            for color_key, pin in self.hardware_config.button_pins.items():
                try:
                    btn_color = ButtonColor(color_key)  # supports str or enum
                except Exception:
                    # As a fallback, attempt upper-case name mapping
                    btn_color = ButtonColor[color_key.upper()]  # type: ignore[index]
                btn = GZButton(pin, pull_up=True, bounce_time=0.05)
                # Capture enum in default arg to avoid late binding
                btn.when_pressed = (lambda c=btn_color: self._handle_press(c))
                btn.when_released = (lambda c=btn_color: self._handle_release(c))
                self._gz_buttons[btn_color] = btn
            self._available = True
            logger.info("GPIO buttons initialized (gpiozero)")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize GPIO buttons (gpiozero): {e}")
            return False

    def _handle_press(self, color: ButtonColor):
        self._button_states[color] = True
        callback = self._press_callbacks.get(color)
        if callback:
            callback(color)
        logger.debug(f"GPIO button {color} pressed")

    def _handle_release(self, color: ButtonColor):
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
    
    # Legacy RPi.GPIO interrupt callback removed; gpiozero event handlers are used instead.


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
            from gpiozero import LED as GZLED  # type: ignore
            self._gz_leds = {}
            # If config has 'led_active_high' and it's False, use active_low LEDs
            active_high = getattr(self.hardware_config, 'led_active_high', True)
            for color, pin in self.hardware_config.led_pins.items():
                if active_high:
                    led = GZLED(pin)
                else:
                    led = GZLED(pin, active_high=False)
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
            # Start internal monitoring only if higher-level service hasn't started its own loop
            # The HardwareManager handles debounced monitoring, so avoid double work here.
            # Keep method available for direct polling via read_switches().
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
                # Short settle; hardware is fast, keep this tiny
                time.sleep(0.0005)
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
                # Keep this lean; main HardwareManager loop also polls
                time.sleep(0.05)  # 20Hz
                
            except Exception as e:
                logger.error(f"Error in switch monitoring: {e}")
                time.sleep(1.0)


class GPIODisplay(DisplayInterface):
    """GPIO 7-segment display implementation (placeholder)."""
    def __init__(self, hardware_config: HardwareConfig):
        self.hardware_config = hardware_config
        self._available = False
        self._last_value = None
        self._brightness = 1.0
        self._tm = None  # Lazy-initialized TM1637 instance

    def initialize(self) -> bool:
        """Initialize TM1637 display using python-tm1637 (gpio)."""
        if not HAS_GPIO:
            logger.error("gpiozero not available; cannot initialize TM1637 display")
            return False
        try:
            # Import locally to avoid import issues on non-Linux dev machines
            from tm1637 import TM1637  # type: ignore
        except Exception as e:
            logger.error(f"python-tm1637 not available: {e}")
            return False

        try:
            clk = int(self.hardware_config.display_clk_pin)
            dio = int(self.hardware_config.display_dio_pin)
            self._tm = TM1637(clk=clk, dio=dio)
            # Apply initial brightness mapping (0-1 -> 0-7)
            self._apply_tm_brightness(self._brightness)
            self._available = True
            logger.info(f"TM1637 display initialized on CLK={clk}, DIO={dio}")
            # Clear on startup
            self.clear()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize TM1637 display: {e}")
            self._tm = None
            self._available = False
            return False

    def cleanup(self) -> None:
        try:
            if self._tm is not None:
                # Best-effort clear and release
                try:
                    if hasattr(self._tm, 'clear'):
                        self._tm.clear()
                    else:
                        self._tm.show('    ')
                except Exception:
                    pass
            self._tm = None
        finally:
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    def show_number(self, value: int, brightness: float = 1.0) -> None:
        """Display a number (0-9999) on the TM1637."""
        if not self.is_available or self._tm is None:
            return
        if not 0 <= value <= 9999:
            raise ValueError(f"Display value must be 0-9999, got {value}")
        try:
            self._last_value = value
            self._brightness = brightness
            self._apply_tm_brightness(brightness)
            # Common libraries support .number(); if unavailable, use .show(str)
            if hasattr(self._tm, 'number'):
                self._tm.number(value)
            else:
                s = str(value).rjust(4)
                if hasattr(self._tm, 'show'):
                    self._tm.show(s)
            logger.debug(f"TM1637 display number: {value} (brightness: {brightness})")
        except Exception as e:
            logger.error(f"Error displaying number on TM1637: {e}")

    def show_text(self, text: str, brightness: float = 1.0) -> None:
        """Display text (first 4 chars best-effort)."""
        if not self.is_available or self._tm is None:
            return
        try:
            self._last_value = text
            self._brightness = brightness
            self._apply_tm_brightness(brightness)
            s = (text or "")[:4].ljust(4)
            # Prefer encode_string/write if available for better segment mapping
            if hasattr(self._tm, 'encode_string') and hasattr(self._tm, 'write'):
                try:
                    encoded = self._tm.encode_string(s)
                    self._tm.write(encoded)
                except Exception:
                    # Fallback to show
                    if hasattr(self._tm, 'show'):
                        self._tm.show(s)
            elif hasattr(self._tm, 'show'):
                self._tm.show(s)
            logger.debug(f"TM1637 display text: '{s}' (brightness: {brightness})")
        except Exception as e:
            logger.error(f"Error displaying text on TM1637: {e}")

    def clear(self) -> None:
        self._last_value = None
        if not self.is_available or self._tm is None:
            return
        try:
            if hasattr(self._tm, 'clear'):
                self._tm.clear()
            elif hasattr(self._tm, 'show'):
                self._tm.show('    ')
            logger.debug("TM1637 display cleared")
        except Exception as e:
            logger.error(f"Error clearing TM1637 display: {e}")

    def set_brightness(self, brightness: float) -> None:
        self._brightness = brightness
        if not self.is_available or self._tm is None:
            return
        try:
            self._apply_tm_brightness(brightness)
            logger.debug(f"TM1637 brightness set: {brightness}")
        except Exception as e:
            logger.error(f"Error setting TM1637 brightness: {e}")

    # --- Internal helpers ---
    def _apply_tm_brightness(self, brightness: float) -> None:
        """Map 0.0-1.0 to TM1637 brightness steps (0-7) and apply."""
        try:
            level = int(round(max(0.0, min(1.0, float(brightness))) * 7))
        except Exception:
            level = 7
        tm = self._tm
        if tm is None:
            return
        try:
            if hasattr(tm, 'brightness'):
                # Some libs use .brightness(level)
                tm.brightness(level)
            elif hasattr(tm, 'set_brightness'):
                tm.set_brightness(level)
        except Exception:
            # Non-fatal if brightness cannot be applied
            pass


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
