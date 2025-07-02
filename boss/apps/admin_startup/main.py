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
    # Blink all LEDs
    for color in ['red', 'yellow', 'green', 'blue']:
        api.led_on(color)
    time.sleep(0.5)
    for color in ['red', 'yellow', 'green', 'blue']:
        api.led_off(color)
    # Show 'Ready' message
    api.display_text(
        "ready",
        align='center',
        color=(0, 255, 0),
        size=64
    )
    # Exit immediately after displaying
    time.sleep(0.5)
