"""Local Tide Times mini-app.

Shows next tide extremes using WorldTides API. Refresh every 3h.
"""
from __future__ import annotations
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
    requests = None  # type: ignore

API_URL = "https://www.worldtides.info/api"


def fetch_tides(api_key: str | None, lat: float, lon: float, timeout: float = 6.0):
    if requests is None:
        raise RuntimeError("requests not available")
    params = {"lat": lat, "lon": lon, "extremes": "true"}
    if api_key:
        params["key"] = api_key
    r = requests.get(API_URL, params=params, timeout=timeout)
    r.raise_for_status()
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
    if not lines:
        raise ValueError("No extremes data")
    return lines


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    from boss.config.secrets_manager import secrets
    api_key = cfg.get("api_key") or secrets.get("BOSS_APP_WORLDTIDES_API_KEY")
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
        try:
            lines = fetch_tides(api_key, lat, lon, timeout=timeout)
            body = "\n".join(lines[:6])
            api.screen.display_text(f"{title}\n\n{body}", align="left")
        except Exception as e:
            api.screen.display_text(f"{title}\n\nErr: {e}", align="left")

    def on_button(event_type, payload):
        nonlocal last_fetch
        if payload.get("button") == "green":
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
