"""Top Trending Search mini-app.

Fetches trending search term from local backend service.
"""
from __future__ import annotations
import time
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


def fetch_trend(url: str, timeout: float = 5.0):
    if requests is None:
        raise RuntimeError("requests not available")
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    trend = data.get("trend")
    if not trend:
        raise ValueError("No trend field")
    return trend


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    url = cfg.get("backend_url", "http://localhost:3000/toptrends")
    refresh_seconds = float(cfg.get("refresh_seconds", 3600))
    timeout = float(cfg.get("request_timeout_seconds", 5))

    api.screen.clear_screen()
    title = "Trending"
    api.screen.display_text(title, font_size=24, align="center")
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show():
        try:
            trend = fetch_trend(url, timeout=timeout)
            api.screen.display_text(f"{title}\n\n" + shorten(trend, width=200, placeholder="…"), align="left")
        except Exception as e:
            api.screen.display_text(f"{title}\n\nErr: {_summarize_error(e)}", align="left")

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
