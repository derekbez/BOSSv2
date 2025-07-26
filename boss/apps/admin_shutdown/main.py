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
    api.hardware.set_led('yellow', True)
    api.hardware.set_led('blue', True)
    api.hardware.set_led('green', True)
    api.hardware.set_led('red', False)
    
    # Display prompt on screen
    api.screen.clear_screen()
    api.screen.display_text(prompt, font_size=16, align="left")
    
    def on_button_press(event_type, event):
        # Only respond to button press, not release
        if event_type != 'button_pressed':
            return
        button = event.get('button_id') or event.get('button')
        
        if button == 'yellow':
            api.screen.clear_screen()
            api.screen.display_text("Rebooting system...", font_size=16, align="center")
            api.log_info("AdminShutdown: Reboot triggered by user.")
            api.event_bus.publish('system_shutdown', {'reason': 'reboot'}, 'admin_shutdown')
            stop_event.set()
            
        elif button == 'blue':
            api.screen.clear_screen()
            api.screen.display_text("Shutting down system...", font_size=16, align="center")
            api.log_info("AdminShutdown: Poweroff triggered by user.")
            api.event_bus.publish('system_shutdown', {'reason': 'poweroff'}, 'admin_shutdown')
            stop_event.set()
            
        elif button == 'green':
            api.screen.clear_screen()
            api.screen.display_text("Exiting to OS shell...", font_size=16, align="center")
            api.log_info("AdminShutdown: Exit to OS triggered by user.")
            api.event_bus.publish('system_shutdown', {'reason': 'exit_to_os'}, 'admin_shutdown')
            stop_event.set()

    # Subscribe to button events
    sub_id = api.event_bus.subscribe(
        'button_pressed',
        on_button_press
    )

    try:
        # Wait for stop_event, but also check every 0.2s for responsiveness
        while not stop_event.is_set():
            stop_event.wait(0.2)
    finally:
        api.event_bus.unsubscribe(sub_id)
        api.hardware.set_led('yellow', False)
        api.hardware.set_led('blue', False)
        api.hardware.set_led('green', False)
        api.hardware.set_led('red', False)
        api.screen.clear_screen()
