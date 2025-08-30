"""Color of the Day mini-app.

Fetches a random color from ColourLovers (XML) and displays name + hex.
Refresh with green button; otherwise daily (very infrequent).
"""
from __future__ import annotations
import time
import xml.etree.ElementTree as ET

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

API_URL = "https://www.colourlovers.com/api/colors/random?format=xml"


def fetch_color(timeout: float = 6.0):
    if requests is None:
        return None
    try:
        r = requests.get(API_URL, timeout=timeout, headers={"User-Agent": "BOSS-Color/1.0"})
        if r.status_code == 200:
            root = ET.fromstring(r.text)
            color = root.find("color")
            if color is not None:
                title = (color.findtext("title") or "?").strip()
                hexcode = (color.findtext("hex") or "??????").strip()
                return title, hexcode
    except Exception:
        return None
    return None


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    refresh_seconds = float(cfg.get("refresh_seconds", 86400))
    timeout = float(cfg.get("request_timeout_seconds", 6))

    api.screen.clear_screen()
    api.screen.write_line("Color of Day", 0)
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show_color():
        api.screen.clear_body(start_line=1)
        c = fetch_color(timeout=timeout)
        if not c:
            api.screen.write_wrapped("(network error)", start_line=2)
            return
        title, hexcode = c
        api.screen.write_line(title[: api.screen.width - 1], 2)
        api.screen.write_line(f"#{hexcode}"[: api.screen.width - 1], 3)

    def on_button(ev):
        nonlocal last_fetch
        if ev.get("button") == "green":
            last_fetch = time.time()
            show_color()

    sub_ids.append(api.event_bus.subscribe("button_pressed", on_button))

    try:
        show_color()
        last_fetch = time.time()
        while not stop_event.is_set():
            now = time.time()
            if now - last_fetch >= refresh_seconds:
                last_fetch = now
                show_color()
            time.sleep(0.5)
    finally:
        for sid in sub_ids:
            api.event_bus.unsubscribe(sid)
        api.hardware.set_led("green", False)
        api.screen.clear_screen()
