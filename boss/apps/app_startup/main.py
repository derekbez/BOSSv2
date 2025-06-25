"""
Startup mini-app for B.O.S.S.
Clears the screen, blinks all four LEDs, and displays 'ready' on the screen using the advanced screen API.
"""
import time

def run(stop_event, api, **kwargs):
    """
    Args:
        stop_event: threading.Event to signal app termination
        api: object with .screen and .leds
    """
    screen = getattr(api, 'screen', None)
    leds = getattr(api, 'leds', None)
    if screen:
        screen.clear()
        # Use advanced display options: center, color, size, bold
        screen.display_text(
            "ready",
            align='center',
            color=(0, 255, 0),
            size=64,
            bold=True
        )
    if leds:
        for led in leds.values():
            try:
                led.on()
            except Exception:
                pass
        time.sleep(0.5)
        for led in leds.values():
            try:
                led.off()
            except Exception:
                pass
    # Wait until stop_event is set (app terminated)
    # if stop_event:
    #     stop_event.wait()
