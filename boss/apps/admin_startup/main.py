"""
Admin startup mini-app for B.O.S.S.
Clears the screen, blinks all four LEDs, and displays 'ready' on the screen using the advanced screen API.
"""
import time

def run(stop_event, api, **kwargs):
    """
    Admin startup mini-app for B.O.S.S.
    Clears the screen, blinks all four LEDs 3 times, and displays 'BOSS Ready' on the screen.
    Args:
        stop_event: threading.Event to signal app termination
        api: AppAPI instance
    """
    api.log_info("Admin Startup: Initializing")
    # Clear the screen
    api.screen.clear_screen()

    led_colors = ["red", "yellow", "green", "blue"]

    def set_all_leds(state: bool):
        for color in led_colors:
            api.hardware.set_led(color, state)

    # Blink all LEDs 3 times
    for i in range(3):
        if stop_event.is_set():
            break
        api.log_info(f"Admin Startup: LED blink {i+1}/3")
        set_all_leds(True)
        if stop_event.wait(0.25):
            break
        set_all_leds(False)
        if stop_event.wait(0.2):
            break

    # Show 'BOSS Ready' message
    api.screen.display_text(
        "BOSS Ready",
        align='center',
        color='green',
        font_size=32
    )
    api.log_info("Admin Startup: Displayed 'BOSS Ready'")

    # Wait briefly before exit
    stop_event.wait(0.5)
