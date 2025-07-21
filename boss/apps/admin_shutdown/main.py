"""
Mini-app: Admin Shutdown
Provides UI for graceful shutdown, reboot, or exit to OS.
Entry point: run(stop_event, api)
"""
from threading import Event
from typing import Any

def run(stop_event: Event, api: Any) -> None:
    """
    Presents shutdown options and handles button presses (event-driven).
    Args:
        stop_event (Event): Event to signal app termination.
        api (AppAPI): Provided API for hardware/display access.
    """
    prompt = (
        "Shutdown Menu:\n"
        "Select shutdown option using:\n"
        "  [YELLOW] Reboot\n"
        "  [BLUE] Poweroff\n"
        "  [GREEN] Exit to OS\n"
    )
    
    # Set LEDs to indicate available options
    api.set_leds({'yellow': True, 'blue': True, 'green': True, 'red': False})
    
    # Display prompt on screen
    api.screen.clear()
    api.screen.print_line(prompt)
    
    def on_button_press(event_type, event):
        # Only respond to button press, not release
        if event_type != 'input.button.pressed':
            return
        button = event.get('button_id') or event.get('button')
        
        if button == 'yellow':
            api.screen.clear()
            api.screen.print_line("Rebooting system...")
            api.logger.info("AdminShutdown: Reboot triggered by user.")
            api.event_bus.publish('system_shutdown', {'reason': 'reboot'}, 'admin_shutdown')
            stop_event.set()
            
        elif button == 'blue':
            api.screen.clear()
            api.screen.print_line("Shutting down system...")
            api.logger.info("AdminShutdown: Poweroff triggered by user.")
            api.event_bus.publish('system_shutdown', {'reason': 'poweroff'}, 'admin_shutdown')
            stop_event.set()
            
        elif button == 'green':
            api.screen.clear()
            api.screen.print_line("Exiting to OS shell...")
            api.logger.info("AdminShutdown: Exit to OS triggered by user.")
            api.event_bus.publish('system_shutdown', {'reason': 'exit_to_os'}, 'admin_shutdown')
            stop_event.set()

    # Subscribe to button events
    sub_id = api.event_bus.subscribe(
        'input.button.pressed',
        on_button_press,
        filter=None
    )

    try:
        # Wait for stop_event, but also check every 0.2s for responsiveness
        while not stop_event.is_set():
            stop_event.wait(0.2)
    finally:
        api.event_bus.unsubscribe(sub_id)
        api.set_leds({'yellow': False, 'blue': False, 'green': False, 'red': False})
        api.screen.clear()
