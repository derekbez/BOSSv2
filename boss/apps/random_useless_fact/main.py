"""Random Useless Fact mini-app.

Periodically (or on green button) fetches and displays a useless fact.
Uses https://uselessfacts.jsph.pl/ API (no key) with graceful error fallback.
"""
from __future__ import annotations
from typing import Any
import time
from textwrap import shorten

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

API_URL = "https://uselessfacts.jsph.pl/random.json?language=en"


def fetch_fact(timeout: float = 5.0) -> str | None:
    if requests is None:
        return None
    try:
        r = requests.get(API_URL, timeout=timeout, headers={"Accept": "application/json"})
        if r.status_code == 200:
            data: dict[str, Any] = r.json()
            fact = data.get("text") or data.get("fact")
            if fact:
                return fact.strip()
    except Exception:
        return None
    return None


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
        fact = fetch_fact(timeout=request_timeout)
        if not fact:
            api.screen.display_text(f"{title}\n\n(network error fetching fact)", align="left")
            return
        api.screen.display_text(f"{title}\n\n" + shorten(fact, width=220, placeholder="…"), align="left")

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
