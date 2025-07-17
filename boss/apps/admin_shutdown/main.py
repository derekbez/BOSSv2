"""
Mini-app: Admin Shutdown
Provides UI for graceful shutdown, reboot, or exit to OS.
Entry point: run(stop_event, api)
"""
from threading import Event
from typing import Any

def run(stop_event: Event, api: Any) -> None:
    api.log_event(f"[admin_shutdown] api.event_bus is: {repr(getattr(api, 'event_bus', None))}")
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


    def on_button_press(event_type, event):
        # Only respond to button press, not release
        if event_type != 'input.button.pressed':
            return
        button = event.get('button_id') or event.get('button')
        if button == 'yellow':
            api.display_text("Rebooting system...")
            api.log_event("AdminShutdown: Reboot triggered by user.")
            if api.event_bus:
                api.log_event("Publishing system_shutdown event: reboot")
                api.event_bus.publish('system_shutdown', {'reason': 'reboot'})
                api.log_event("Published system_shutdown event: reboot")
            stop_event.set()
        elif button == 'blue':
            api.display_text("Shutting down system...")
            api.log_event("AdminShutdown: Poweroff triggered by user.")
            if api.event_bus:
                api.log_event("Publishing system_shutdown event: poweroff")
                api.event_bus.publish('system_shutdown', {'reason': 'poweroff'})
                api.log_event("Published system_shutdown event: poweroff")
            stop_event.set()
        elif button == 'green':
            api.display_text("Exiting to OS shell...")
            api.log_event("AdminShutdown: Exit to OS triggered by user.")
            if api.event_bus:
                api.log_event("Publishing system_shutdown event: exit_to_os")
                api.event_bus.publish('system_shutdown', {'reason': 'exit_to_os'})
                api.log_event("Published system_shutdown event: exit_to_os")
            stop_event.set()

    sub_id = api.event_bus.subscribe(
        'input.button.pressed',
        on_button_press,
        filter=None  # Let handler filter for robustness
    )

    try:
        # Wait for stop_event, but also check every 0.2s for responsiveness
        while not stop_event.is_set():
            stop_event.wait(0.2)
    finally:
        api.event_bus.unsubscribe(sub_id)
        if hasattr(api, 'set_leds'):
            api.set_leds({'yellow': False, 'blue': False, 'green': False})
        api.display_text("")
