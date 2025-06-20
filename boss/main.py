"""
B.O.S.S. Main Entry Point
Initializes core systems, logging, hardware, and handles clean shutdown.
"""

import sys
import signal
import json
from boss.core.logger import get_logger
from boss.core.app_manager import AppManager
from boss.core.app_runner import AppRunner
from boss.hardware.pins import *
from boss.hardware.display import MockSevenSegmentDisplay, PiSevenSegmentDisplay
from boss.hardware.switch_reader import MockSwitchReader, PiSwitchReader, KeyboardSwitchReader, KeyboardGoButton
import time
from gpiozero import Device

# Try to import real hardware libraries, fallback to mocks if unavailable
try:
    from gpiozero.pins.lgpio import LGPIOFactory
    Device.pin_factory = LGPIOFactory()
except ImportError:
    pass  # Fallback to default pin factory if lgpio is not available

try:
    from gpiozero import Button as PiButton, LED as PiLED
    import tm1637
    REAL_HARDWARE = True
except ImportError:
    from boss.hardware.button import MockButton as PiButton
    from boss.hardware.led import MockLED as PiLED
    REAL_HARDWARE = False

logger = get_logger("BOSS")

# Hardware device instances (global for cleanup)
btn_red = None
btn_yellow = None
btn_green = None
btn_blue = None
main_btn = None
led_red = None
led_yellow = None
led_green = None
led_blue = None
display = None
switch_reader = None

def initialize_hardware():
    global btn_red, btn_yellow, btn_green, btn_blue, main_btn
    global led_red, led_yellow, led_green, led_blue
    global display, switch_reader
    logger.info("Initializing hardware interfaces...")
    if REAL_HARDWARE:
        try:
            btn_red = PiButton(BTN_RED_PIN)
            btn_yellow = PiButton(BTN_YELLOW_PIN)
            btn_green = PiButton(BTN_GREEN_PIN)
            btn_blue = PiButton(BTN_BLUE_PIN)
            main_btn = PiButton(MAIN_BTN_PIN)
            led_red = PiLED(LED_RED_PIN)
            led_yellow = PiLED(LED_YELLOW_PIN)
            led_green = PiLED(LED_GREEN_PIN)
            led_blue = PiLED(LED_BLUE_PIN)
        except Exception as e:
            logger.warning(f"Button/LED hardware init failed: {e}. Falling back to mocks.")
            from boss.hardware.button import MockButton as PiButton
            from boss.hardware.led import MockLED as PiLED
            btn_red = PiButton("red")
            btn_yellow = PiButton("yellow")
            btn_green = PiButton("green")
            btn_blue = PiButton("blue")
            main_btn = KeyboardGoButton()
            led_red = PiLED("red")
            led_yellow = PiLED("yellow")
            led_green = PiLED("green")
            led_blue = PiLED("blue")
        # 7-segment display check
        try:
            display = PiSevenSegmentDisplay(TM_CLK_PIN, TM_DIO_PIN)
            display.show_number(88)  # Test write
        except Exception as e:
            logger.warning(f"7-segment display not detected: {e}. Using mock display.")
            display = MockSevenSegmentDisplay()
        # Multiplexer check
        try:
            switch_reader = PiSwitchReader([MUX1_PIN, MUX2_PIN, MUX3_PIN], MUX_IN_PIN)
            test_val = switch_reader.read_value()
            if test_val == 0:
                logger.warning("Multiplexer read returned 0. MUX may not be connected. Using keyboard input.")
                switch_reader = KeyboardSwitchReader(1)
        except Exception as e:
            logger.warning(f"Multiplexer not detected: {e}. Using keyboard input.")
            switch_reader = KeyboardSwitchReader(1)
        # Go button check
        try:
            if main_btn.is_pressed() not in [True, False]:
                raise Exception("Go button read did not return a boolean.")
        except Exception as e:
            logger.warning(f"Go button not detected: {e}. Using keyboard input.")
            main_btn = KeyboardGoButton()
    else:
        btn_red = PiButton("red")
        btn_yellow = PiButton("yellow")
        btn_green = PiButton("green")
        btn_blue = PiButton("blue")
        main_btn = KeyboardGoButton()
        led_red = PiLED("red")
        led_yellow = PiLED("yellow")
        led_green = PiLED("green")
        led_blue = PiLED("blue")
        display = MockSevenSegmentDisplay()
        switch_reader = KeyboardSwitchReader(1)
    logger.info("Hardware initialized.")

def cleanup():
    logger.info("Performing clean shutdown and resource cleanup...")
    for dev in [btn_red, btn_yellow, btn_green, btn_blue, main_btn,
                led_red, led_yellow, led_green, led_blue, display, switch_reader]:
        if hasattr(dev, 'close'):
            try:
                dev.close()
            except Exception:
                pass
    logger.info("Shutdown complete.")

def main():
    logger.info("B.O.S.S. system starting up.")
    try:
        initialize_hardware()
        # Load app mappings
        with open("boss/config/BOSSsettings.json") as f:
            config = json.load(f)
        app_mappings = config.get("app_mappings", {})
        # Use mocks for now; replace with real hardware as needed
        switch = switch_reader if switch_reader else MockSwitchReader(1)
        seg_display = display if display else MockSevenSegmentDisplay()
        print(f"[DEBUG] {switch}")
        app_manager = AppManager(switch, seg_display)
        app_runner = AppRunner()
        last_value = None
        last_btn_state = False
        logger.info("System running. Press Ctrl+C to exit.")
        print("[DEBUG] Entering main event loop...")
        signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
        while True:
            print("[DEBUG] Polling switch and button...")
            value = app_manager.poll_and_update_display()
            print(f"[DEBUG] Switch value: {value}")
            print("[DEBUG] About to check Go button state...")
            try:
                btn_state = main_btn.is_pressed() if main_btn else False
                print(f"[DEBUG] Go button state: {btn_state}")
            except Exception as e:
                print(f"[DEBUG] Exception in is_pressed(): {e}")
                raise
            # Debounce: detect rising edge
            if btn_state and not last_btn_state:
                app_name = app_mappings.get(str(value))
                print(f"[DEBUG] Launching app: {app_name} for value {value}")
                if app_name:
                    class MockScreen:
                        def clear(self):
                            print("[MOCK SCREEN] clear")
                        def display_text(self, text, align='center'):
                            print(f"[MOCK SCREEN] {text}")
                    api = type('API', (), {'screen': MockScreen()})()
                    app_runner.run_app(app_name, api=api)
            last_btn_state = btn_state
            time.sleep(0.1)
    except SystemExit:
        cleanup()
        logger.info("System exited cleanly.")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()