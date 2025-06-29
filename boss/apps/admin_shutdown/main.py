"""
Mini-app: Admin Shutdown
Provides UI for graceful shutdown, reboot, or exit to OS.
Entry point: run(stop_event, api)
"""
import os
from threading import Event
from typing import Any

def run(stop_event: Event, api: Any) -> None:
    """
    Presents shutdown options and handles button presses.
    Args:
        stop_event (Event): Event to signal app termination.
        api (object): Provided API for hardware/display access.
    """
    prompt = (
        "Shutdown Menu:\n"
        "Select shutdown option using:\n"
        "  [YELLOW] Reboot\n"
        "  [BLUE] Poweroff\n"
        "  [GREEN] Exit to OS\n"
    )
    api.led_on('yellow')
    api.led_on('blue')
    api.led_on('green')
    api.screen.display_text(prompt)
    while not stop_event.is_set():
        btn = api.wait_for_button(['yellow', 'blue', 'green'], timeout=0.2)
        if btn == 'yellow':
            api.screen.display_text("Rebooting system...")
            api.log_event("AdminShutdown: Reboot triggered by user.")
            api.led_off('yellow')
            api.led_off('blue')
            api.led_off('green')
            os.system('sudo reboot')
            break
        elif btn == 'blue':
            api.screen.display_text("Shutting down system...")
            api.log_event("AdminShutdown: Poweroff triggered by user.")
            api.led_off('yellow')
            api.led_off('blue')
            api.led_off('green')
            os.system('sudo poweroff')
            break
        elif btn == 'green':
            api.screen.display_text("Exiting to OS shell...")
            api.log_event("AdminShutdown: Exit to OS triggered by user.")
            api.led_off('yellow')
            api.led_off('blue')
            api.led_off('green')
            break
    # If stop_event is set, clean up
    api.led_off('yellow')
    api.led_off('blue')
    api.led_off('green')
    api.screen.display_text("")
