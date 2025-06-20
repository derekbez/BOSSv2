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
    hardware_status = {}
    pin_info = {
        'BTN_RED_PIN': BTN_RED_PIN,
        'BTN_YELLOW_PIN': BTN_YELLOW_PIN,
        'BTN_GREEN_PIN': BTN_GREEN_PIN,
        'BTN_BLUE_PIN': BTN_BLUE_PIN,
        'MAIN_BTN_PIN': MAIN_BTN_PIN,
        'LED_RED_PIN': LED_RED_PIN,
        'LED_YELLOW_PIN': LED_YELLOW_PIN,
        'LED_GREEN_PIN': LED_GREEN_PIN,
        'LED_BLUE_PIN': LED_BLUE_PIN,
        'TM_CLK_PIN': TM_CLK_PIN,
        'TM_DIO_PIN': TM_DIO_PIN,
        'MUX1_PIN': MUX1_PIN,
        'MUX2_PIN': MUX2_PIN,
        'MUX3_PIN': MUX3_PIN,
        'MUX_IN_PIN': MUX_IN_PIN,
    }
    print("[BOSS] Pin assignments:")
    logger.info("Pin assignments:")
    for name, val in pin_info.items():
        print(f"  {name}: {val}")
        logger.info(f"  {name}: {val}")
    if REAL_HARDWARE:
        # Buttons
        try:
            btn_red = PiButton(BTN_RED_PIN)
            hardware_status['btn_red'] = 'OK'
        except Exception as e:
            btn_red = KeyboardGoButton()
            hardware_status['btn_red'] = f"MOCK ({e})"
        try:
            btn_yellow = PiButton(BTN_YELLOW_PIN)
            hardware_status['btn_yellow'] = 'OK'
        except Exception as e:
            btn_yellow = KeyboardGoButton()
            hardware_status['btn_yellow'] = f"MOCK ({e})"
        try:
            btn_green = PiButton(BTN_GREEN_PIN)
            hardware_status['btn_green'] = 'OK'
        except Exception as e:
            btn_green = KeyboardGoButton()
            hardware_status['btn_green'] = f"MOCK ({e})"
        try:
            btn_blue = PiButton(BTN_BLUE_PIN)
            hardware_status['btn_blue'] = 'OK'
        except Exception as e:
            btn_blue = KeyboardGoButton()
            hardware_status['btn_blue'] = f"MOCK ({e})"
        try:
            main_btn = PiButton(MAIN_BTN_PIN)
            hardware_status['main_btn'] = 'OK'
        except Exception as e:
            main_btn = KeyboardGoButton()
            hardware_status['main_btn'] = f"MOCK ({e})"
        # LEDs
        try:
            led_red = PiLED(LED_RED_PIN)
            hardware_status['led_red'] = 'OK'
        except Exception as e:
            led_red = PiLED("red")
            hardware_status['led_red'] = f"MOCK ({e})"
        try:
            led_yellow = PiLED(LED_YELLOW_PIN)
            hardware_status['led_yellow'] = 'OK'
        except Exception as e:
            led_yellow = PiLED("yellow")
            hardware_status['led_yellow'] = f"MOCK ({e})"
        try:
            led_green = PiLED(LED_GREEN_PIN)
            hardware_status['led_green'] = 'OK'
        except Exception as e:
            led_green = PiLED("green")
            hardware_status['led_green'] = f"MOCK ({e})"
        try:
            led_blue = PiLED(LED_BLUE_PIN)
            hardware_status['led_blue'] = 'OK'
        except Exception as e:
            led_blue = PiLED("blue")
            hardware_status['led_blue'] = f"MOCK ({e})"
        # 7-segment display
        try:
            display = PiSevenSegmentDisplay(TM_CLK_PIN, TM_DIO_PIN)
            display.show_number(88)
            hardware_status['display'] = 'OK'
        except Exception as e:
            display = MockSevenSegmentDisplay()
            hardware_status['display'] = f"MOCK ({e})"
        # Multiplexer
        try:
            switch_reader = PiSwitchReader([MUX1_PIN, MUX2_PIN, MUX3_PIN], MUX_IN_PIN)
            test_val = switch_reader.read_value()
            if test_val == 0:
                raise Exception("MUX read returned 0")
            hardware_status['switch_reader'] = 'OK'
        except Exception as e:
            switch_reader = KeyboardSwitchReader(1)
            hardware_status['switch_reader'] = f"MOCK ({e})"
        # Go button check (redundant, but for summary)
        try:
            # FIX: is_pressed is a property, not a method
            if main_btn.is_pressed not in [True, False]:
                raise Exception("Go button read did not return a boolean.")
            hardware_status['go_button'] = 'OK'
        except Exception as e:
            main_btn = KeyboardGoButton()
            hardware_status['go_button'] = f"MOCK ({e})"
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
        for k in ['btn_red','btn_yellow','btn_green','btn_blue','main_btn','led_red','led_yellow','led_green','led_blue','display','switch_reader','go_button']:
            hardware_status[k] = 'MOCK (dev mode)'
    logger.info("Hardware initialized.")
    logger.info("Hardware startup summary:")
    for k, v in hardware_status.items():
        print(f"  {k}: {v}")
        logger.info(f"  {k}: {v}")
    # --- Startup LED blink and welcome message ---
    # Blink each LED in turn
    for led in [led_red, led_yellow, led_green, led_blue]:
        try:
            led.on()
            time.sleep(0.2)
            led.off()
            time.sleep(0.1)
        except Exception as e:
            logger.warning(f"LED blink failed: {e}")
    # Show welcome message on 7-segment display
    try:
        display.show_message("BOSS")
        time.sleep(1.0)
        display.show_message("----")
        time.sleep(0.5)
    except Exception as e:
        logger.warning(f"Display welcome message failed: {e}")

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
        switch = switch_reader if switch_reader else MockSwitchReader(1)
        seg_display = display if display else MockSevenSegmentDisplay()
        app_manager = AppManager(switch, seg_display)
        app_runner = AppRunner()
        last_value = None
        last_btn_state = False
        logger.info("System running. Press Ctrl+C to exit.")
        signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
        while True:
            value = app_manager.poll_and_update_display()
            try:
                btn_state = main_btn.is_pressed if main_btn else False
            except Exception as e:
                logger.error(f"Exception in is_pressed(): {e}")
                raise
            # Debounce: detect rising edge
            if btn_state and not last_btn_state:
                app_name = app_mappings.get(str(value))
                logger.info(f"Launching app: {app_name} for value {value}")
                if app_name:
                    class MockScreen:
                        def clear(self):
                            logger.info("[MOCK SCREEN] clear")
                        def display_text(self, text, align='center'):
                            logger.info(f"[MOCK SCREEN] {text}")
                    api = type('API', (), {'screen': MockScreen()})()
                    app_runner.run_app(app_name, api=api)
            else:
                # If no app is running, show "Ready" on the main screen
                try:
                    display.show_message("Ready")
                except Exception:
                    pass
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