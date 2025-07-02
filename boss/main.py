"""
B.O.S.S. Main Entry Point
Initializes core systems, logging, hardware, and handles clean shutdown.
"""

import sys
import signal
import json
import logging
import logging.handlers
from boss.core.logger import get_logger
from boss.core.app_manager import AppManager
from boss.core.app_runner import AppRunner
from boss.core.event_bus import EventBus
from boss.core.event_bus_config import EventBusConfig
from boss.hardware.pins import *
from boss.hardware.display import MockSevenSegmentDisplay, PiSevenSegmentDisplay
from boss.hardware.switch_reader import MockSwitchReader, PiSwitchReader, KeyboardSwitchReader, KeyboardGoButton
from boss.hardware.screen import MockScreen
from boss.hardware.pillow_screen import PillowScreen
from boss.core.paths import CONFIG_PATH
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
    #import rpi_tm1637
    REAL_HARDWARE = True
except ImportError:
    from boss.hardware.button import MockButton as PiButton
    from boss.hardware.led import MockLED as PiLED
    REAL_HARDWARE = False

# Configure logging ONCE for the whole application
def setup_logging():
    """Configure logging for the entire application"""
    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    root_logger = logging.getLogger()
    # Avoid duplicate handlers if setup_logging is called more than once
    if not root_logger.handlers:
        root_logger.setLevel(logging.INFO)  # Change to DEBUG for more verbosity
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        root_logger.addHandler(console_handler)
        # File handler - rotate files at 1MB
        # NOTE: This writes to the current working directory. Change path if needed.
        file_handler = logging.handlers.RotatingFileHandler(
            'boss/logs/boss.log',
            maxBytes=1024*1024,
            backupCount=2  # Keep 2 backup files
        )
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        root_logger.addHandler(file_handler)

# Set up logging before anything else
setup_logging()
logger = logging.getLogger(__name__)

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
screen = None

def hide_os_cursor():
    """Hide the OS-level blinking cursor on the main console (tty1), only if running on tty1."""
    try:
        if os.isatty(0):
            tty = os.ttyname(0)
            if tty == '/dev/tty1':
                os.system('setterm -cursor off > /dev/tty1 2>/dev/null')
                os.system('echo -ne "\033[999;999H" > /dev/tty1 2>/dev/null')
    except Exception as e:
        logger.warning(f"Failed to hide OS cursor: {e}")

def show_os_cursor():
    """Re-enable the OS-level blinking cursor on the main console (tty1), only if running on tty1."""
    try:
        if os.isatty(0):
            tty = os.ttyname(0)
            if tty == '/dev/tty1':
                os.system('setterm -cursor on > /dev/tty1 2>/dev/null')
    except Exception as e:
        logger.warning(f"Failed to re-enable OS cursor: {e}")

def initialize_hardware():
    global btn_red, btn_yellow, btn_green, btn_blue, main_btn
    global led_red, led_yellow, led_green, led_blue
    global display, switch_reader, screen
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
            # event_bus will be injected after EventBus is created
            display = PiSevenSegmentDisplay(TM_CLK_PIN, TM_DIO_PIN)
            display.show_message("BOSS")
            hardware_status['display'] = 'OK'
        except Exception as e:
            display = MockSevenSegmentDisplay()
            hardware_status['display'] = f"MOCK ({e})"
        # Multiplexer
        try:
            switch_reader = PiSwitchReader([MUX1_PIN, MUX2_PIN, MUX3_PIN], MUX_IN_PIN)
            # Try reading multiple times to ensure the mux is responsive
            test_vals = [switch_reader.read_value() for _ in range(3)]
            # If all reads raise an exception, it will be caught below
            hardware_status['switch_reader'] = 'OK'
        except Exception as e:
            switch_reader = KeyboardSwitchReader(1)
            hardware_status['switch_reader'] = f"MOCK ({e})"
        # Screen check
        try:
            # Use PillowScreen for HDMI framebuffer
            from boss.hardware.pillow_screen import PillowScreen
            screen = PillowScreen()
            logger.info("Screen: PillowScreen initialized (HDMI framebuffer)")
        except Exception as e:
            screen = MockScreen()
            logger.warning(f"Screen not detected: {e}. Using mock screen.")
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
        # Use PygameScreen for dev if available
        try:
            from boss.hardware.pillow_screen import PillowScreen
            screen = PillowScreen()
            logger.info("Screen: PillowScreen initialized (dev mode)")
        except Exception as e:
            screen = MockScreen()
            logger.info("Screen: MockScreen initialized (dev mode)")
        for k in ['btn_red','btn_yellow','btn_green','btn_blue','main_btn','led_red','led_yellow','led_green','led_blue','display','switch_reader','go_button']:
            hardware_status[k] = 'MOCK (dev mode)'
    logger.info("Hardware initialized.")
    logger.info("Hardware startup summary:")
    for k, v in hardware_status.items():
        print(f"  {k}: {v}")
        logger.info(f"  {k}: {v}")
    # --- Startup LED blink and welcome message ---
    # (Moved LED blinking to admin_startup mini-app)
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
    # Show shutdown message on 7-segment display
    try:
        if display:
            display.show_message("----")
    except Exception:
        pass
    for dev in [btn_red, btn_yellow, btn_green, btn_blue, main_btn,
                led_red, led_yellow, led_green, led_blue, display, switch_reader]:
        if hasattr(dev, 'close'):
            try:
                dev.close()
            except Exception:
                pass
    # Ensure PygameScreen or PillowScreen is closed and thread joined
    if screen and hasattr(screen, 'close'):
        try:
            screen.clear()
            screen.close()
        except Exception:
            pass
    # Clear the screen back to OS (do this after closing framebuffer)
    # try:
    #     os.system('clear')
    # except Exception:
    #     pass
    # Re-enable cursor on exit
    show_os_cursor()
    logger.info("Shutdown complete.")

def main():
    logger.info("B.O.S.S. system starting up.")
    hide_os_cursor()  # Hide cursor at startup
    try:
        initialize_hardware()
        # Set up EventBus with config (log all events by default)
        event_bus = EventBus(EventBusConfig(log_all_events=True))
        # Inject event_bus into display (for event-driven publishing)
        if hasattr(display, 'event_bus'):
            display.event_bus = event_bus
        # Register core event types
        event_bus.register_event_type("app_started", {"app_name": str, "version": str, "timestamp": str})
        event_bus.register_event_type("app_stopped", {"app_name": str, "version": str, "timestamp": str})
        event_bus.register_event_type("switch_change", {"value": int, "previous_value": int, "timestamp": str})
        # Register shutdown and error event types
        event_bus.register_event_type("system_shutdown", {"reason": str, "timestamp": str})
        event_bus.register_event_type("error", {"error_type": str, "message": str, "stack_trace": str, "timestamp": str})

        # Subscribe display to output.display.updated events (event-driven display updates)
        def on_display_update(event_type, payload):
            val = payload.get("value")
            if val is not None:
                # Try to show as number if possible, else as message
                try:
                    n = int(val)
                    display.show_number(n)
                except Exception:
                    display.show_message(str(val))
        event_bus.subscribe("output.display.updated", on_display_update)

        # Run startup mini-app before anything else
        try:
            from boss.apps import admin_startup
            import threading
            from boss.core.api import AppAPI
            leds = {'red': led_red, 'yellow': led_yellow, 'green': led_green, 'blue': led_blue}
            buttons = {'red': btn_red, 'yellow': btn_yellow, 'green': btn_green, 'blue': btn_blue}
            api = AppAPI(screen=screen, buttons=buttons, leds=leds, event_bus=event_bus, logger=logger)
            stop_event = threading.Event()
            admin_startup.run(stop_event, api=api)
        except Exception as e:
            logger.warning(f"Startup app failed: {e}")
        # Load app mappings and initialize managers
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        app_mappings = config.get("app_mappings", {})
        switch = switch_reader if switch_reader else MockSwitchReader(1)
        seg_display = display if display else MockSevenSegmentDisplay()
        app_manager = AppManager(switch, seg_display, event_bus=event_bus)
        app_runner = AppRunner(event_bus=event_bus)
        logger.info("System running. Press Ctrl+C to exit.")
        signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
        from boss.core.api import AppAPI
        leds = {'red': led_red, 'yellow': led_yellow, 'green': led_green, 'blue': led_blue}
        buttons = {'red': btn_red, 'yellow': btn_yellow, 'green': btn_green, 'blue': btn_blue}
        api = AppAPI(screen=screen, buttons=buttons, leds=leds, event_bus=event_bus, logger=logger)

        # --- Event-driven Go button logic ---
        # Subscribe to main Go button press events via EventBus
        def on_go_button_pressed(event_type, payload):
            # Only handle the main Go button
            if payload.get("button_id") == "main":
                value = app_manager.poll_and_update_display()
                app_name = app_mappings.get(str(value))
                logger.info(f"Go button pressed (event). Switch value: {value}, launching app: {app_name}")
                if app_name:
                    app_runner.run_app(app_name, api=api)
                else:
                    logger.info(f"No app mapped for value {value}.")

        event_bus.subscribe("input.button.pressed", on_go_button_pressed)

        # Main loop: just keep the process alive, all logic is now event-driven
        while True:
            time.sleep(0.1)
    except SystemExit:
        if 'event_bus' in locals():
            event_bus.publish_system_shutdown("SystemExit")
        cleanup()
        logger.info("System exited cleanly.")
        raise
    except Exception as e:
        import traceback
        if 'event_bus' in locals():
            event_bus.publish_error(type(e).__name__, str(e), stack_trace=traceback.format_exc())
        logger.exception(f"Fatal error: {e}")
        cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()