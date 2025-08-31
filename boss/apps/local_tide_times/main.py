"""Local Tide Times mini-app.

Shows next tide extremes using WorldTides API. Refresh every 3h.
"""
from __future__ import annotations
import time
from textwrap import shorten

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

API_URL = "https://www.worldtides.info/api"


def fetch_tides(api_key: str | None, lat: float, lon: float, timeout: float = 6.0):
    if requests is None:
        return None
    params = {"lat": lat, "lon": lon, "extremes": ""}
    if api_key:
        params["key"] = api_key
    try:
        r = requests.get(API_URL, params=params, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            tides = data.get("extremes", [])
            lines = []
            for t in tides[:4]:
                date = t.get("date") or "?"
                typ = t.get("type") or "?"
                if date and len(date) >= 16:
                    clock = date[11:16]
                else:
                    clock = date
                lines.append(f"{clock} {typ}")
            return lines
    except Exception:
        return None
    return None


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    api_key = cfg.get("api_key") or api.get_config_value("WORLDTIDES_API_KEY")
    lat = float(cfg.get("latitude", 51.5074))
    lon = float(cfg.get("longitude", -0.1278))
    refresh_seconds = float(cfg.get("refresh_seconds", 10800))
    timeout = float(cfg.get("request_timeout_seconds", 6))

    api.screen.clear_screen()
    title = "Tides"
    api.screen.display_text(title, font_size=24, align="center")
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show():
        lines = fetch_tides(api_key, lat, lon, timeout=timeout)
        if not lines:
            api.screen.display_text(f"{title}\n\n(error/no data)", align="left")
            return
        body = "\n".join(shorten(l, width=40, placeholder="…") for l in lines[:6])
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
