"""Moon Phase mini-app.

Shows current moon phase and illumination using ipgeolocation.io.
Refresh every 6h or via green button.
"""
from __future__ import annotations
import time

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

API_URL = "https://api.ipgeolocation.io/astronomy"


from typing import Dict, Any
import os


def fetch_data(api_key: str | None, lat: float, lon: float, timeout: float = 6.0):
    if requests is None:
        return None
    params: Dict[str, Any] = {"lat": lat, "long": lon}
    if api_key:
        params["apiKey"] = api_key
    try:
        r = requests.get(API_URL, params=params, timeout=timeout)
        if r.status_code == 200:
            d = r.json()
            return {
                "phase": d.get("moon_phase"),
                "illum": d.get("moon_illumination"),
                "rise": d.get("moonrise"),
                "set": d.get("moonset"),
            }
    except Exception:
        return None
    return None


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    # Canonical env var name per secrets convention
    api_key = (
        cfg.get("api_key")
        or os.environ.get("BOSS_APP_IPGEO_API_KEY")
        or api.get_config_value("IPGEO_API_KEY")  # legacy fallback if still set
    )
    lat = float(cfg.get("latitude", 51.5074))
    lon = float(cfg.get("longitude", -0.1278))
    refresh_seconds = float(cfg.get("refresh_seconds", 21600))
    timeout = float(cfg.get("request_timeout_seconds", 6))

    api.screen.clear_screen()
    title = "Moon Phase"
    api.screen.display_text(title, font_size=24, align="center")
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show():
        info = fetch_data(api_key, lat, lon, timeout=timeout)
        if not info:
            api.screen.display_text(f"{title}\n\n(error/no data)", align="left")
            return
        body = f"{info['phase']}\nIllum {info['illum']}%\n\nRise {info['rise']}\nSet  {info['set']}"
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
