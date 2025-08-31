"""Tiny Poem mini-app.

Fetches a short poem via Poemist API. Refresh every 3h or manual.

Enhancements (2025-08-31):
* Raw error display (no generic fallback message).
* No truncation of poem content; full text shown (wrapped).
* Basic wrapping utility; future paging can reuse approach from other apps.
"""
from __future__ import annotations
import time
import textwrap

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

API_URL = "https://www.poemist.com/api/v1/randompoems"


def fetch_poem(timeout: float = 6.0):
    if requests is None:
        raise RuntimeError("requests not available")
    r = requests.get(API_URL, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if not data:
        raise ValueError("Empty poem list")
    p = data[0]
    title = p.get("title") or "Poem"
    content = (p.get("content") or "").strip()
    author = (p.get("poet") or {}).get("name") or "?"
    return title, content, author


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    refresh_seconds = float(cfg.get("refresh_seconds", 10800))
    timeout = float(cfg.get("request_timeout_seconds", 6))

    api.screen.clear_screen()
    title = "Tiny Poem"
    api.screen.display_text(title, font_size=26, align="center")
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show():
        try:
            pt, content, author = fetch_poem(timeout=timeout)
            wrap_width = int(cfg.get("wrap_width", 60))
            wrapped = textwrap.wrap(content, width=wrap_width) or [content]
            lines = [title, "", pt] + wrapped + ["", f"- {author}"]
            api.screen.display_text("\n".join(lines), align="left")
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
