"""Quote of the Day mini-app.

Shows a quote then waits for a button press to fetch a new one.
Network errors are handled gracefully with a fallback message.
"""
from __future__ import annotations
from typing import Any
import json
import time
from textwrap import shorten

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover - requests may be absent in some test envs
    requests = None  # type: ignore

from boss.apps._error_utils import summarize_error

API_URL = "https://api.quotable.io/random"


def fetch_quote(timeout: float = 5.0) -> tuple[str, str]:
    if requests is None:
        raise RuntimeError("requests not available")
    r = requests.get(API_URL, timeout=timeout)
    r.raise_for_status()
    data: dict[str, Any] = r.json()
    content = data.get("content") or data.get("quote")
    if not content:
        raise ValueError("No quote content")
    author = data.get("author") or data.get("authorName") or ""
    return content, author


def run(stop_event, api):  # signature required by platform
    cfg = api.get_app_config() or {}
    refresh_timeout = float(cfg.get("request_timeout_seconds", 5))
    api.screen.clear_screen()
    title = "Quote of the Day"
    api.screen.display_text(title, font_size=26, align="center")

    api.hardware.set_led("green", True)  # green=fetch new
    sub_ids = []

    def show_quote():
        try:
            text, author = fetch_quote(timeout=refresh_timeout)
            body = shorten(text, width=240, placeholder="…")
            lines = [title, "", body]
            if author:
                lines.append("")
                lines.append(f"- {author}")
            api.screen.display_text("\n".join(lines), align="left")
        except Exception as e:
            api.screen.display_text(f"{title}\n\nErr: {e}", align="left")

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
