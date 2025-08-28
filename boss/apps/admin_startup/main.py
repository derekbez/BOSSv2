"""
Admin Startup Mini-App
======================

Purpose:
- Provide immediate visual confirmation on boot with a short LED animation
  and a simple screen message.

Notes:
- 7-segment display is system-controlled; this app does not modify it.
- Uses stop_event-aware waits to allow fast shutdown.
- Ensures LEDs are turned off before exit.
"""

import time


def run(stop_event, api, **kwargs):
    """
    Run the admin startup sequence.

    Args:
        stop_event: threading.Event to signal app termination
        api: AppAPI instance
    """
    api.log_info("Admin Startup: Initializing")

    # Clear screen and show a brief starting message
    try:
        api.screen.clear_screen()
        api.screen.display_text("Starting BOSS…", font_size=32, align="center")
    except Exception as e:
        api.log_error(f"Admin Startup: Screen init error: {e}")

    led_colors = ["red", "yellow", "green", "blue"]

    def set_all_leds(state: bool):
        for color in led_colors:
            try:
                api.hardware.set_led(color, state)
            except Exception:
                pass

    def blink_all(times: int = 2, on_sec: float = 0.2, off_sec: float = 0.15):
        for i in range(times):
            if stop_event.is_set():
                return
            api.log_info(f"Admin Startup: LED blink {i + 1}/{times}")
            set_all_leds(True)
            if stop_event.wait(on_sec):
                return
            set_all_leds(False)
            if stop_event.wait(off_sec):
                return

    try:
        # Short, simple animation
        blink_all(times=2, on_sec=0.22, off_sec=0.16)

        # Final message
        api.screen.display_text("BOSS Ready", align="left", color="green", font_size=48)
        api.log_info("Admin Startup: Displayed 'BOSS Ready'")

        # Small grace period; exit early if asked
        stop_event.wait(0.4)

    finally:
        # Ensure LEDs are off on exit
        set_all_leds(False)
