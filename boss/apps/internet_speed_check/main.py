"""Internet Speed Check mini-app (placeholder).

Future enhancement: integrate speedtest module. Currently shows placeholder
values and resamples every refresh interval.
"""
from __future__ import annotations
import random
import time


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    refresh_seconds = float(cfg.get("refresh_seconds", 1800))

    api.screen.clear_screen()
    title = "Net Speed"
    api.screen.display_text(title, font_size=24, align="center")
    api.hardware.set_led("green", True)

    last_fetch = 0.0

    def show():
        down = random.uniform(20, 120)
        up = random.uniform(10, 40)
        ping = random.uniform(10, 60)
        api.screen.display_text(f"{title}\n\nDown {down:0.1f} Mbps\nUp   {up:0.1f} Mbps\nPing {ping:0.0f} ms", align="left")

    show()
    last_fetch = time.time()

    try:
        while not stop_event.is_set():
            if time.time() - last_fetch >= refresh_seconds:
                last_fetch = time.time()
                show()
            time.sleep(0.5)
    finally:
        api.hardware.set_led("green", False)
        api.screen.clear_screen()
