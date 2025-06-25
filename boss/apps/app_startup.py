"""
Startup mini-app for B.O.S.S.
Clears the screen, blinks all four LEDs, and displays 'ready' on the screen.
"""
def run(api, leds=None, screen=None, **kwargs):
    # Accepts api object with .screen, and optionally a dict of leds
    import time
    if screen is None and hasattr(api, 'screen'):
        screen = api.screen
    if leds is None and hasattr(api, 'leds'):
        leds = api.leds
    if screen:
        screen.clear()
        screen.display_text("ready")
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
    else:
        # Fallback: print to console
        print("[STARTUP] Blinking LEDs and displaying 'ready' on screen.")
