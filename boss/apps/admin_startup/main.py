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
    # Clear the screen
    api.screen.clear_screen()
    
    # Blink all LEDs
    for color in ['red', 'yellow', 'green', 'blue']:
        api.hardware.set_led(color, True)
    time.sleep(0.5)
    for color in ['red', 'yellow', 'green', 'blue']:
        api.hardware.set_led(color, False)
    
    # Show 'Ready' message
    api.screen.display_text(
        "BOSS Ready",
        align='center',
        color='green',
        font_size=32
    )
    
    # Exit immediately after displaying - no button input expected
    # LEDs should remain off since no user interaction needed
    time.sleep(0.5)
