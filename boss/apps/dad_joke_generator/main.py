"""Dad Joke Generator mini-app.

Fetches a dad joke periodically or via green button from icanhazdadjoke.
"""
from __future__ import annotations
import time

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

API_URL = "https://icanhazdadjoke.com/"
HEADERS = {"Accept": "application/json", "User-Agent": "BOSS-DadJoke/1.0"}


def fetch_joke(timeout: float = 6.0) -> str | None:
    if requests is None:
        return None
    try:
        r = requests.get(API_URL, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            joke = data.get("joke")
            if joke:
                return joke.strip()
    except Exception:
        return None
    return None


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    refresh_seconds = float(cfg.get("refresh_seconds", 300))
    timeout = float(cfg.get("request_timeout_seconds", 6))

    api.screen.clear_screen()
    title = "Dad Joke"
    api.screen.display_text(title, font_size=24, align="center")
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show_joke():
        joke = fetch_joke(timeout=timeout)
        if not joke:
            api.screen.display_text(f"{title}\n\n(network error)", align="left")
            return
        api.screen.display_text(f"{title}\n\n{joke}", align="left")

    def on_button(event_type, payload):
        nonlocal last_fetch
        if payload.get("button") == "green":
            last_fetch = time.time()
            show_joke()

    sub_ids.append(api.event_bus.subscribe("button_pressed", on_button))

    try:
        show_joke()
        last_fetch = time.time()
        while not stop_event.is_set():
            now = time.time()
            if now - last_fetch >= refresh_seconds:
                last_fetch = now
                show_joke()
            time.sleep(0.25)
    finally:
        for sid in sub_ids:
            api.event_bus.unsubscribe(sid)
        api.hardware.set_led("green", False)
        api.screen.clear_screen()
