"""Random Useless Fact mini-app.

Periodically (or on green button) fetches and displays a useless fact.
Uses https://uselessfacts.jsph.pl/ API (no key) with graceful error fallback.
"""
from __future__ import annotations
from typing import Any
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

API_URL = "https://uselessfacts.jsph.pl/random.json?language=en"


def fetch_fact(timeout: float = 5.0) -> str:
    if requests is None:
        raise RuntimeError("requests not available")
    r = requests.get(API_URL, timeout=timeout, headers={"Accept": "application/json"})
    r.raise_for_status()
    data: dict[str, Any] = r.json()
    fact = data.get("text") or data.get("fact")
    if not fact:
        raise ValueError("No fact in response")
    return fact.strip()


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    refresh_seconds = float(cfg.get("refresh_seconds", 45))
    request_timeout = float(cfg.get("request_timeout_seconds", 6))

    api.screen.clear_screen()
    title = "Random Fact"
    api.screen.display_text(title, font_size=24, align="center")
    api.hardware.set_led("green", True)  # green for refresh

    sub_ids = []
    last_fetch = 0.0

    def show_fact():
        try:
            fact = fetch_fact(timeout=request_timeout)
            api.screen.display_text(f"{title}\n\n{fact}", align="left")
        except Exception as e:
            api.screen.display_text(f"{title}\n\nErr: {e}", align="left")

    def on_button(event):
        nonlocal last_fetch
        if event.get("button") == "green":
            last_fetch = time.time()
            show_fact()

    sub_ids.append(api.event_bus.subscribe("button_pressed", on_button))

    try:
        show_fact()
        last_fetch = time.time()
        while not stop_event.is_set():
            now = time.time()
            if now - last_fetch >= refresh_seconds:
                last_fetch = now
                show_fact()
            time.sleep(0.2)
    finally:
        for sid in sub_ids:
            api.event_bus.unsubscribe(sid)
        for c in ["red", "yellow", "green", "blue"]:
            api.hardware.set_led(c, False)
        api.screen.clear_screen()
