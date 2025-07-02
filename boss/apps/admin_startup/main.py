"""
Admin startup mini-app for B.O.S.S.
Clears the screen, blinks all four LEDs, and displays 'ready' on the screen using the advanced screen API.
"""
import time

def run(stop_event, api, **kwargs):
    """
    Args:
        stop_event: threading.Event to signal app termination
        api: AppAPI instance
    """
    if hasattr(api.screen, 'clear'):
        api.screen.clear()
    # Use advanced display options: center, color, size
    api.display_text(
        "ready",
        align='center',
        color=(0, 255, 0),
        size=64
    )
    # Blink all LEDs
    for color in ['red', 'yellow', 'green', 'blue']:
        api.led_on(color)
    time.sleep(0.5)
    for color in ['red', 'yellow', 'green', 'blue']:
        api.led_off(color)
    # Wait for any button press to continue (event-driven)
    pressed = []
    def on_any_button(event):
        pressed.append(event.get('button_id'))
        stop_event.set()
    sub_id = api.event_bus.subscribe('input.button.pressed', on_any_button)
    try:
        while not stop_event.is_set():
            stop_event.wait(0.2)
    finally:
        api.event_bus.unsubscribe(sub_id)
