"""On This Day mini-app.

Shows notable events for today's date using byabbe.se API.
Refresh infrequently (half-day) or manually via green button.
"""
from __future__ import annotations
import datetime as _dt
import time
from textwrap import shorten

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore


def fetch_events(month: int, day: int, timeout: float = 6.0):
    if requests is None:
        return None
    url = f"https://byabbe.se/on-this-day/{month}/{day}/events.json"
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            events = data.get("events", [])
            lines = []
            for e in events[:6]:
                year = e.get("year") or "?"
                desc = (e.get("description") or "")[:60]
                if desc:
                    lines.append(f"{year}: {desc}")
            return lines
    except Exception:
        return None
    return None


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    refresh_seconds = float(cfg.get("refresh_seconds", 43200))  # half day
    timeout = float(cfg.get("request_timeout_seconds", 6))

    api.screen.clear_screen()
    title = "On This Day"
    api.screen.display_text(title, font_size=22, align="center")
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show():
        today = _dt.date.today()
        lines = fetch_events(today.month, today.day, timeout=timeout)
        if not lines:
            api.screen.display_text(f"{title}\n\n(no events / error)", align="left")
            return
        body = "\n".join(shorten(l, width=60, placeholder="…") for l in lines[:8])
        api.screen.display_text(f"{title}\n\n{body}", align="left")

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
