"""current_weather - Periodic weather snapshot via Open-Meteo.

Network-enabled reference mini-app.
"""
from __future__ import annotations
from typing import Any, Dict
from threading import Event
import json
import time

def _summarize_error(err: Exception) -> str:
    resp = getattr(err, 'response', None)
    if resp is not None and hasattr(resp, 'status_code'):
        try:
            reason = getattr(resp, 'reason', '') or ''
            msg = f"HTTP {resp.status_code} {reason}".strip()
        except Exception:
            msg = ''
    else:
        msg = str(err) or err.__class__.__name__
    if not msg:
        msg = err.__class__.__name__
    if len(msg) > 60:
        msg = msg[:57] + '...'
    return msg

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # fallback handled at runtime


def fetch_weather(lat: float, lon: float, timeout: float) -> Dict[str, Any]:
    if requests is None:
        raise RuntimeError("requests not available")
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True
    }
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def format_weather(data: Dict[str, Any]) -> str:
    cw = data.get("current_weather", {}) if data else {}
    t = cw.get("temperature")
    w = cw.get("windspeed")
    c = cw.get("cloudcover") if "cloudcover" in cw else cw.get("cloud_cover")
    def fmt(v, suffix=""):
        return f"{v}{suffix}" if v is not None else "?"
    return f"Temp: {fmt(t, '°C')}\nWind: {fmt(w, ' km/h')}\nCloud: {fmt(c, '%')}"


def run(stop_event: Event, api: Any) -> None:
    api.log_info("current_weather starting")
    cfg = api.get_app_config(default={}) or {}
    lat = float(cfg.get("latitude", 51.5074))
    lon = float(cfg.get("longitude", -0.1278))
    refresh = int(cfg.get("refresh_seconds", 60))
    timeout = float(cfg.get("request_timeout_seconds", 4))

    def render_message(msg: str) -> None:
        api.screen.clear_screen()
        api.screen.display_text(msg, align="center")

    last_fetch_ok = False
    last_good_msg = ""

    while not stop_event.is_set():
        try:
            data = fetch_weather(lat, lon, timeout)
            msg = format_weather(data)
            last_fetch_ok = True
            last_good_msg = msg
            render_message(msg)
        except Exception as e:
            emsg = _summarize_error(e)
            api.log_error(f"Weather fetch failed: {e}")
            if not last_fetch_ok:
                render_message(f"Weather error:\n{emsg}")
            else:
                render_message(f"{last_good_msg}\nErr: {emsg}")
        # Wait in small increments to be responsive to stop_event
        slept = 0
        while slept < refresh and not stop_event.wait(0.5):
            slept += 0.5

    api.log_info("current_weather stopping")
