"""Top Trending Search mini-app.

Fetches trending search term from local backend service.
"""
from __future__ import annotations
import time

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore


def fetch_trend(url: str, timeout: float = 5.0):
    if requests is None:
        return None
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            return data.get("trend") or None
    except Exception:
        return None
    return None


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    url = cfg.get("backend_url", "http://localhost:3000/toptrends")
    refresh_seconds = float(cfg.get("refresh_seconds", 3600))
    timeout = float(cfg.get("request_timeout_seconds", 5))

    api.screen.clear_screen()
    api.screen.write_line("Trending", 0)
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show():
        api.screen.clear_body(start_line=1)
        trend = fetch_trend(url, timeout=timeout)
        if not trend:
            api.screen.write_wrapped("(no trend / error)", start_line=2)
            return
        api.screen.write_wrapped(trend, start_line=2)

    def on_button(ev):
        nonlocal last_fetch
        if ev.get("button") == "green":
            last_fetch = time.time()
            show()

    sub_ids.append(api.event_bus.subscribe("button_pressed", on_button))

    try:
        show()
        last_fetch = time.time()
        while not stop_event.is_set():
            if time.time() - last_fetch >= refresh_seconds:
                last_fetch = time.time()
                show()
            time.sleep(0.5)
    finally:
        for sid in sub_ids:
            api.event_bus.unsubscribe(sid)
        api.hardware.set_led("green", False)
        api.screen.clear_screen()
