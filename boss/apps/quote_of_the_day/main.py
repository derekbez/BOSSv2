"""Quote of the Day mini-app.

Shows a quote then waits for a button press to fetch a new one.
Network errors are handled gracefully with a fallback message.
"""
from __future__ import annotations
from typing import Any
import json
import time

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover - requests may be absent in some test envs
    requests = None  # type: ignore

API_URL = "https://api.quotable.io/random"


def fetch_quote(timeout: float = 5.0) -> tuple[str, str] | None:
    if requests is None:
        return None
    try:
        r = requests.get(API_URL, timeout=timeout)
        if r.status_code == 200:
            data: dict[str, Any] = r.json()
            content = data.get("content") or data.get("quote")
            author = data.get("author") or data.get("authorName") or ""  # some APIs
            if content:
                return content, author
    except Exception:
        return None
    return None


def run(stop_event, api):  # signature required by platform
    cfg = api.get_app_config() or {}
    refresh_timeout = float(cfg.get("request_timeout_seconds", 5))
    api.screen.clear_screen()
    api.screen.write_line("Quote of the Day", 0)

    api.hardware.set_led("green", True)  # green=fetch new
    sub_ids = []

    def show_quote():
        api.screen.clear_body(start_line=1)
        q = fetch_quote(timeout=refresh_timeout)
        if not q:
            api.screen.write_wrapped("(network error fetching quote)", start_line=2)
            return
        text, author = q
        api.screen.write_wrapped(text, start_line=2)
        if author:
            api.screen.write_line(f"- {author}", api.screen.height - 2)

    def on_button(event):
        if event.get("button") == "green":
            show_quote()

    sub_ids.append(api.event_bus.subscribe("button_pressed", on_button))

    try:
        show_quote()
        while not stop_event.is_set():
            time.sleep(0.1)
    finally:
        for sid in sub_ids:
            api.event_bus.unsubscribe(sid)
        for c in ["red", "yellow", "green", "blue"]:
            api.hardware.set_led(c, False)
        api.screen.clear_screen()
