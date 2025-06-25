"""
[DEPRECATED] Use the folder-based mini-app in app_startup/ with manifest.json and main.py.
This file remains for backward compatibility only.
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
