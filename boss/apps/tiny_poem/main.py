"""Tiny Poem mini-app.

Fetches a short poem via Poemist API. Refresh every 3h or manual.
"""
from __future__ import annotations
import time

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

API_URL = "https://www.poemist.com/api/v1/randompoems"


def fetch_poem(timeout: float = 6.0):
    if requests is None:
        return None
    try:
        r = requests.get(API_URL, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            if data:
                p = data[0]
                title = p.get("title") or "Poem"
                content = (p.get("content") or "")[:120]
                author = (p.get("poet") or {}).get("name") or "?"
                return title, content, author
    except Exception:
        return None
    return None


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    refresh_seconds = float(cfg.get("refresh_seconds", 10800))
    timeout = float(cfg.get("request_timeout_seconds", 6))

    api.screen.clear_screen()
    api.screen.write_line("Tiny Poem", 0)
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show():
        api.screen.clear_body(start_line=1)
        result = fetch_poem(timeout=timeout)
        if not result:
            api.screen.write_wrapped("(error/no data)", start_line=2)
            return
        title, content, author = result
        api.screen.write_line(title[: api.screen.width - 1], 2)
        api.screen.write_wrapped(content, start_line=3, max_lines=4)
        api.screen.write_line(f"- {author}"[: api.screen.width - 1], 8)

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
