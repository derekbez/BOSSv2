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
    Presents shutdown options and handles button presses (event-driven).
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
    if hasattr(api, 'set_leds'):
        api.set_leds({'yellow': True, 'blue': True, 'green': True})
    api.display_text(prompt)

    def on_button_press(event):
        button = event.get('button_id')
        if button == 'yellow':
            api.display_text("Rebooting system...")
            api.log_event("AdminShutdown: Reboot triggered by user.")
            if hasattr(api, 'set_leds'):
                api.set_leds({'yellow': False, 'blue': False, 'green': False})
            os.system('sudo reboot')
            stop_event.set()
        elif button == 'blue':
            api.display_text("Shutting down system...")
            api.log_event("AdminShutdown: Poweroff triggered by user.")
            if hasattr(api, 'set_leds'):
                api.set_leds({'yellow': False, 'blue': False, 'green': False})
            os.system('sudo poweroff')
            stop_event.set()
        elif button == 'green':
            api.display_text("Exiting to OS shell...")
            api.log_event("AdminShutdown: Exit to OS triggered by user.")
            if hasattr(api, 'set_leds'):
                api.set_leds({'yellow': False, 'blue': False, 'green': False})
            stop_event.set()

    sub_id = api.event_bus.subscribe(
        'input.button.pressed',
        on_button_press,
        filter={"button_id": ["yellow", "blue", "green"]}
    )

    try:
        while not stop_event.is_set():
            stop_event.wait(0.2)
    finally:
        api.event_bus.unsubscribe(sub_id)
        if hasattr(api, 'set_leds'):
            api.set_leds({'yellow': False, 'blue': False, 'green': False})
        api.display_text("")
