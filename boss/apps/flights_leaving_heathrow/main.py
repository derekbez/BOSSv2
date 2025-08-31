"""Flights Leaving Heathrow mini-app.

Shows limited list of departing flights using Aviationstack API.
"""
from __future__ import annotations
import time
from typing import Any

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

API_URL = "http://api.aviationstack.com/v1/flights"


def fetch_flights(api_key: str | None, timeout: float = 6.0, limit: int = 8):
    if requests is None:
        return None
    params = {"dep_iata": "LHR", "limit": limit}
    if api_key:
        params["access_key"] = api_key
    try:
        r = requests.get(API_URL, params=params, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            flights = data.get("data", [])
            lines = []
            for f in flights:
                airline = (f.get("airline") or {}).get("name") or "?"
                code = (f.get("flight") or {}).get("iata") or "?"
                sched = (f.get("departure") or {}).get("scheduled") or "?"
                if sched and len(sched) >= 16:
                    sched = sched[11:16]
                lines.append(f"{code} {sched} {airline}")
                if len(lines) >= limit:
                    break
            return lines
    except Exception:
        return None
    return None


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    api_key = cfg.get("api_key") or api.get_config_value("AVIATIONSTACK_API_KEY")
    timeout = float(cfg.get("request_timeout_seconds", 6))
    refresh_seconds = float(cfg.get("refresh_seconds", 600))

    api.screen.clear_screen()
    title = "LHR Departures"
    api.screen.display_text(title, font_size=22, align="center")
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show():
        lines = fetch_flights(api_key, timeout=timeout)
        if not lines:
            api.screen.display_text(f"{title}\n\n(no data / error)", align="left")
            return
        body = "\n".join(lines[:8])
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
