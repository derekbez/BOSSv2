# --- Web UI for debugging (only in mock mode) ---
# (Removed maybe_start_web_ui, now handled in hardware init)
"""
B.O.S.S. Main Entry Point
Initializes core systems, logging, hardware, and handles clean shutdown.
"""

# --- Standard library imports ---
import sys
import signal
import json
import logging
import logging.handlers
import time
import os

# --- BOSS imports ---
from boss.core.logger import get_logger
from boss.core.app_manager import AppManager
from boss.core.app_runner import AppRunner
from boss.core.event_bus import EventBus
from boss.core.event_bus_config import EventBusConfig
from boss.hardware.pins import *
from boss.hardware.display import MockSevenSegmentDisplay, PiSevenSegmentDisplay
from boss.hardware.switch_reader import MockSwitchReader, PiSwitchReader, APISwitchReader
from boss.hardware.button import APIButton
from boss.hardware.screen import get_screen
from boss.core.paths import CONFIG_PATH

# Web UI debug dashboard import (only used in mock mode)
def start_web_ui(hardware):
    try:
        from boss.webui.main import start_web_ui as _start_web_ui
        _start_web_ui(hardware)
    except Exception as e:
        logger.warning(f"Could not start web UI debug dashboard: {e}")

# --- Hardware import fallback logic ---

# Import SwitchMonitor (no hardware dependency)
from boss.hardware.switch_monitor import SwitchMonitor


# Try to import real hardware libraries, fallback to mocks if unavailable

# Hardware abstraction: always use mocks on non-Linux or if import fails
import platform
if platform.system() == "Linux":
    try:
        from gpiozero import Button as PiButton, LED as PiLED
        REAL_HARDWARE = True
    except ImportError:
        from boss.hardware.button import MockButton as PiButton
        from boss.hardware.led import MockLED as PiLED
        REAL_HARDWARE = False
else:
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
        if hasattr(os, 'isatty') and os.isatty(0):
            # Only attempt on Linux
            if platform.system() == "Linux":
                try:
                    import tty
                    import termios
                    # Hide cursor using ANSI escape
                    print("\033[?25l", end="", flush=True)
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"Failed to hide OS cursor: {e}")

def show_os_cursor():
    """Re-enable the OS-level blinking cursor on the main console (tty1), only if running on tty1."""
    try:
        if hasattr(os, 'isatty') and os.isatty(0):
            if platform.system() == "Linux":
                try:
                    print("\033[?25h", end="", flush=True)
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"Failed to re-enable OS cursor: {e}")


# --- Refactored hardware initialization for lower complexity and no pygame ---
def initialize_hardware(event_bus):
    """Initialize all hardware and start web UI in mock mode. Requires event_bus as argument."""
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
    logger.info("Pin assignments:")
    for name, val in pin_info.items():
        logger.info(f"  {name}: {val}")

    def try_init(real_ctor, fallback_ctor, arg, status_key, event_bus=None, button_id=None):
        try:
            # If the constructor supports event_bus, pass it
            if event_bus is not None and button_id is not None:
                obj = real_ctor(arg, event_bus=event_bus, button_id=button_id)
            elif event_bus is not None:
                obj = real_ctor(arg, event_bus=event_bus)
            else:
                obj = real_ctor(arg)
            hardware_status[status_key] = 'OK'
            return obj
        except Exception as e:
            # Fallback to mock
            if event_bus is not None and button_id is not None:
                obj = fallback_ctor(button_id, event_bus=event_bus, button_id=button_id)
            elif event_bus is not None:
                obj = fallback_ctor(button_id, event_bus=event_bus)
            else:
                obj = fallback_ctor(button_id)
            hardware_status[status_key] = f"MOCK ({e})"
            return obj

    # event_bus must be set before calling this function
    from boss.hardware.button import APIButton, PiButton
    from boss.hardware.led import MockLED, PiLED
    if REAL_HARDWARE:
        btn_red = try_init(PiButton, APIButton, BTN_RED_PIN, 'btn_red', event_bus=event_bus, button_id="red")
        btn_yellow = try_init(PiButton, APIButton, BTN_YELLOW_PIN, 'btn_yellow', event_bus=event_bus, button_id="yellow")
        btn_green = try_init(PiButton, APIButton, BTN_GREEN_PIN, 'btn_green', event_bus=event_bus, button_id="green")
        btn_blue = try_init(PiButton, APIButton, BTN_BLUE_PIN, 'btn_blue', event_bus=event_bus, button_id="blue")
        main_btn = try_init(PiButton, APIButton, MAIN_BTN_PIN, 'main_btn', event_bus=event_bus, button_id="main")
        led_red = try_init(PiLED, PiLED, LED_RED_PIN, 'led_red')
        led_yellow = try_init(PiLED, PiLED, LED_YELLOW_PIN, 'led_yellow')
        led_green = try_init(PiLED, PiLED, LED_GREEN_PIN, 'led_green')
        led_blue = try_init(PiLED, PiLED, LED_BLUE_PIN, 'led_blue')
        try:
            display = PiSevenSegmentDisplay(TM_CLK_PIN, TM_DIO_PIN)
            display.show_message("BOSS")
            hardware_status['display'] = 'OK'
        except Exception as e:
            display = MockSevenSegmentDisplay()
            display.show_message("MOCK")
            hardware_status['display'] = f"MOCK ({e})"
        try:
            switch_reader = PiSwitchReader([MUX1_PIN, MUX2_PIN, MUX3_PIN], MUX_IN_PIN)
            switch_reader.read_value()
            hardware_status['switch_reader'] = 'OK'
        except Exception as e:
            switch_reader = APISwitchReader(1)
            hardware_status['switch_reader'] = f"MOCK ({e})"
        screen = get_screen()
        logger.info(f"Screen: {type(screen).__name__} initialized (HDMI framebuffer)")
    else:
        btn_red = APIButton("red", event_bus=event_bus, button_id="red")
        btn_yellow = APIButton("yellow", event_bus=event_bus, button_id="yellow")
        btn_green = APIButton("green", event_bus=event_bus, button_id="green")
        btn_blue = APIButton("blue", event_bus=event_bus, button_id="blue")
        main_btn = APIButton("main", event_bus=event_bus, button_id="main")
        led_red = MockLED("red")
        led_yellow = MockLED("yellow")
        led_green = MockLED("green")
        led_blue = MockLED("blue")
        display = MockSevenSegmentDisplay()
        switch_reader = APISwitchReader(1)
        screen = get_screen()
        logger.info(f"Screen: {type(screen).__name__} initialized (dev mode)")
        mock_hardware_dict = {
            'btn_red': btn_red,
            'btn_yellow': btn_yellow,
            'btn_green': btn_green,
            'btn_blue': btn_blue,
            'main_btn': main_btn,
            'led_red': led_red,
            'led_yellow': led_yellow,
            'led_green': led_green,
            'led_blue': led_blue,
            'display': display,
            'switch_reader': switch_reader,
            'switch': switch_reader,  # Add alias for web UI compatibility
            'screen': screen,
        }
        try:
            start_web_ui(mock_hardware_dict)
            logger.info("[BOSS] Debug dashboard started at http://localhost:8000 (web UI for mock/dev mode)")
        except Exception as e:
            logger.warning(f"Could not start web UI debug dashboard: {e}")
        for k in mock_hardware_dict:
            hardware_status[k] = 'MOCK (dev mode)'

    logger.info("Hardware initialized.")
    logger.info("Hardware startup summary:")
    for k, v in hardware_status.items():
        #print(f"  {k}: {v}")
        logger.info(f"  {k}: {v}")
    # --- Startup LED blink and welcome message ---
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
            display.show_message("-  -")
    except Exception:
        pass
    for dev in [btn_red, btn_yellow, btn_green, btn_blue, main_btn,
                led_red, led_yellow, led_green, led_blue, display, switch_reader]:
        if hasattr(dev, 'close'):
            try:
                dev.close()
            except Exception:
                pass
    # Ensure PillowScreen is closed and thread joined 
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



from boss.core import event_handlers

# --- Initialization Functions ---
def setup_event_bus():
    eb = EventBus(EventBusConfig(log_all_events=True))
    eb.register_event_type("switch_change", {"value": int, "previous_value": int, "timestamp": str})
    eb.register_event_type("input.switch.set", {"value": int, "timestamp": str})
    eb.register_event_type("app_started", {"app_name": str, "version": str, "timestamp": str})
    eb.register_event_type("app_stopped", {"app_name": str, "version": str, "timestamp": str})
    eb.register_event_type("system_shutdown", {"reason": str, "timestamp": str})
    eb.register_event_type("error", {"error_type": str, "message": str, "stack_trace": str, "timestamp": str})
    return eb

def setup_api(event_bus):
    from boss.core.api import AppAPI
    leds = {'red': led_red, 'yellow': led_yellow, 'green': led_green, 'blue': led_blue}
    buttons = {'red': btn_red, 'yellow': btn_yellow, 'green': btn_green, 'blue': btn_blue}
    # Always inject the real event_bus (main event_bus)
    api = AppAPI(screen=screen, buttons=buttons, leds=leds, event_bus=event_bus, logger=logger)
    logger.info(f"[setup_api] Using event_bus id: {id(event_bus)} for AppAPI")
    return api

def load_config():
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    return config.get("app_mappings", {})

def start_admin_startup_app(app_runner, api):
    try:
        app_runner.run_app("admin_startup", api=api)
    except Exception as e:
        logger.warning(f"Startup app failed: {e}")

from contextlib import contextmanager
@contextmanager
def boss_cleanup():
    try:
        yield
    except SystemExit:
        cleanup()
        logger.info("System exited cleanly.")
        raise
    except Exception as e:
        import traceback
        logger.exception(f"Fatal error: {e}")
        cleanup()
        sys.exit(1)
    # finally:
    #     pass

def main():
    logger.info("B.O.S.S. system starting up.")
    hide_os_cursor()  # Hide cursor at startup
    global event_bus, app_mappings, switch, seg_display, app_runner, api
    event_bus = setup_event_bus()
    initialize_hardware(event_bus)  # Pass event_bus to hardware init
    # Inject event_bus into display if supported
    if display and hasattr(display, 'event_bus'):
        try:
            display.event_bus = event_bus
        except Exception:
            pass
    app_mappings = load_config()
    switch = switch_reader if switch_reader else MockSwitchReader(1)
    seg_display = display if display else MockSevenSegmentDisplay()
    app_runner = AppRunner(event_bus=event_bus)
    api = setup_api(event_bus)
    logger.info(f"[main] Main event_bus id: {id(event_bus)}")
    logger.info(f"[main] AppAPI.event_bus id: {id(getattr(api, 'event_bus', None))}")
    logger.info("System running. Press Ctrl+C to exit.")
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))

    # Register event handlers using imported functions (all async for non-blocking operation)
    event_bus.subscribe("output.display.set",
        lambda event_type, payload: display.show_message(str(payload.get("text"))) if display and hasattr(display, 'show_message') and payload.get("text") is not None else None,
        mode="async"
    )
    event_bus.subscribe("output.led.set", event_handlers.handle_led_set(led_red, led_yellow, led_green, led_blue), mode="async")
    # Subscribe generic button handler for all button presses (logs and enables global actions)
    event_bus.subscribe("input.button.pressed", event_handlers.handle_button_pressed(), mode="async")
    # Subscribe go button handler for launching apps (main button only)
    event_bus.subscribe("input.button.pressed", event_handlers.on_go_button_pressed(switch, app_mappings, app_runner, api), mode="async")
    # Use consolidated display update handler for switch_change only (input.switch.set triggers switch_change via APISwitchReader)
    event_bus.subscribe("switch_change", event_handlers.handle_display_update(seg_display), mode="async")
    # Remove redundant input.switch.set display update; only update switch state
    event_bus.subscribe("input.switch.set", event_handlers.handle_switch_set(switch, display), mode="async")
    event_bus.subscribe(
        "system_shutdown",
        event_handlers.handle_system_shutdown(app_runner, cleanup, logger),
        mode="async"
    )

    # --- Web UI event bus integration ---
    try:
        import asyncio
        from boss.webui.server import ws_manager
        loop = asyncio.get_event_loop()
        def push_all_events(event_type, payload):
            coro = ws_manager.push_event({"type": event_type, "payload": payload})
            try:
                asyncio.run_coroutine_threadsafe(coro, loop)
            except Exception as e:
                logger.warning(f"Failed to schedule ws_manager.push_event: {e}")
        event_bus.subscribe("*", push_all_events, mode="async")  # Subscribe to all events
        ws_manager.hardware["api"] = api
        ws_manager.hardware["event_bus"] = event_bus
    except Exception as e:
        logger.warning(f"Web UI event bus integration failed: {e}")

    # Start admin_startup app
    start_admin_startup_app(app_runner, api)

    # Start switch monitor
    switch_monitor = SwitchMonitor(switch, event_bus)
    switch_monitor.start()

    # Main thread just waits for signals/events
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, EOFError):
        logger.info("Exit signal received (KeyboardInterrupt or EOF). Exiting main loop.")
        cleanup()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}")
        cleanup()
        sys.exit(1)

if __name__ == "__main__":
    # Ensure main() is defined before calling
    try:
        main()
    except NameError as e:
        logger.error(f"main() is not defined: {e}")