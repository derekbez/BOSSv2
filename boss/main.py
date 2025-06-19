"""
B.O.S.S. Main Entry Point
Initializes core systems, logging, hardware, and handles clean shutdown.
"""

import sys
import signal
from boss.core.logger import get_logger
from boss.hardware.pins import *

# Try to import real hardware libraries, fallback to mocks if unavailable
try:
    from gpiozero import Button as PiButton, LED as PiLED
    import tm1637
    REAL_HARDWARE = True
except ImportError:
    from boss.hardware.button import MockButton as PiButton
    from boss.hardware.led import MockLED as PiLED
    from boss.hardware.display import MockSevenSegmentDisplay as PiDisplay
    from boss.hardware.switch_reader import MockSwitchReader as PiSwitchReader
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
        btn_red = PiButton(BTN_RED_PIN)
        btn_yellow = PiButton(BTN_YELLOW_PIN)
        btn_green = PiButton(BTN_GREEN_PIN)
        btn_blue = PiButton(BTN_BLUE_PIN)
        main_btn = PiButton(MAIN_BTN_PIN)
        led_red = PiLED(LED_RED_PIN)
        led_yellow = PiLED(LED_YELLOW_PIN)
        led_green = PiLED(LED_GREEN_PIN)
        led_blue = PiLED(LED_BLUE_PIN)
        display = tm1637.TM1637(clk=TM_CLK_PIN, dio=TM_DIO_PIN)
        # You would implement PiSwitchReader for real hardware
        switch_reader = None  # TODO: Implement PiSwitchReader
    else:
        btn_red = PiButton("red")
        btn_yellow = PiButton("yellow")
        btn_green = PiButton("green")
        btn_blue = PiButton("blue")
        main_btn = PiButton("main")
        led_red = PiLED("red")
        led_yellow = PiLED("yellow")
        led_green = PiLED("green")
        led_blue = PiLED("blue")
        display = PiDisplay()
        switch_reader = PiSwitchReader()
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
        # ...main event loop or app manager...
        logger.info("System running. Press Ctrl+C to exit.")
        signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
        signal.pause()
    except SystemExit:
        cleanup()
        logger.info("System exited cleanly.")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()
