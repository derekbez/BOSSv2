"""Constellation of the Night mini-app.

Currently placeholder static messaging; future enhancement could integrate
with astronomy APIs / local ephemeris.
"""
from __future__ import annotations
import time


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    message = cfg.get("message", "Orion visible tonight! (placeholder)")

    api.screen.clear_screen()
    api.screen.write_line("Constellation", 0)
    api.screen.write_wrapped(message, start_line=2)

    # simple idle loop until stopped
    while not stop_event.is_set():
        time.sleep(0.5)

    api.screen.clear_screen()
