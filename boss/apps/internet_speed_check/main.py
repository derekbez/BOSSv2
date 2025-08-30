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
    api.screen.write_line("Net Speed", 0)
    api.hardware.set_led("green", True)

    last_fetch = 0.0

    def show():
        api.screen.clear_body(start_line=1)
        down = random.uniform(20, 120)
        up = random.uniform(10, 40)
        ping = random.uniform(10, 60)
        api.screen.write_line(f"Down {down:0.1f} Mbps", 2)
        api.screen.write_line(f"Up   {up:0.1f} Mbps", 3)
        api.screen.write_line(f"Ping {ping:0.0f} ms", 5)

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
