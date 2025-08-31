"""Space Update mini-app.

Shows a snippet from NASA APOD or a Mars Rover photo date using NASA APIs.
Refresh every 6h or via green.
"""
from __future__ import annotations
import time
import random
from textwrap import shorten

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

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

APOD_URL = "https://api.nasa.gov/planetary/apod"
MARS_URL = "https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos"


def fetch_space(api_key: str | None, timeout: float = 6.0):
    if requests is None:
        raise RuntimeError("requests not available")
    endpoints = [("apod", APOD_URL), ("mars", MARS_URL)]
    name, url = random.choice(endpoints)
    params = {}
    if api_key:
        params["api_key"] = api_key
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if name == "apod":
        title = data.get("title") or "APOD"
        expl = (data.get("explanation") or "")[:80]
        return f"{title}\n{expl}..."
    photos = data.get("photos", [])
    if photos:
        return f"Mars photo {photos[0].get('earth_date', '')}"
    return "No Mars photos."


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    api_key = cfg.get("api_key") or api.get_config_value("NASA_API_KEY")
    refresh_seconds = float(cfg.get("refresh_seconds", 21600))
    timeout = float(cfg.get("request_timeout_seconds", 6))

    api.screen.clear_screen()
    title = "Space Update"
    api.screen.display_text(title, font_size=26, align="center")
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show():
        try:
            text = fetch_space(api_key, timeout=timeout)
            api.screen.display_text(f"{title}\n\n" + shorten(text, width=240, placeholder="…"), align="left")
        except Exception as e:
            api.screen.display_text(f"{title}\n\nErr: {e}", align="left")

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
