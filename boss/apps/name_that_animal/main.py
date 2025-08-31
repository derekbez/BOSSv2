"""Name That Animal mini-app.

Shows a random animal name + diet from Zoo Animal API.
"""
from __future__ import annotations
import time

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

API_URL = "https://zoo-animal-api.herokuapp.com/animals/rand"


def fetch_animal(timeout: float = 6.0):
    if requests is None:
        return None
    try:
        r = requests.get(API_URL, timeout=timeout)
        if r.status_code == 200:
            d = r.json()
            name = d.get("name") or "?"
            diet = d.get("diet") or "?"
            return name, diet
    except Exception:
        return None
    return None


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    refresh_seconds = float(cfg.get("refresh_seconds", 1800))
    timeout = float(cfg.get("request_timeout_seconds", 6))

    api.screen.clear_screen()
    title = "Animal"
    api.screen.display_text(title, font_size=24, align="center")
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show():
        res = fetch_animal(timeout=timeout)
        if not res:
            api.screen.display_text(f"{title}\n\n(error/no data)", align="left")
            return
        name, diet = res
        api.screen.display_text(f"{title}\n\n{name}\n\n{diet}", align="left")

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
