"""Joke of the Moment mini-app.

Fetches a joke from JokeAPI. For two-part jokes, waits for a button before punchline.
Refreshes periodically or via button.
"""
from __future__ import annotations
import time

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

BASE_URL = "https://v2.jokeapi.dev/joke/"


def fetch_joke(category: str, jtype: str, blacklist: list[str], timeout: float = 6.0):
    if requests is None:
        return None
    params = {"type": jtype, "blacklistFlags": ",".join(blacklist)}
    url = f"{BASE_URL}{category}"
    try:
        r = requests.get(url, params=params, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    category = cfg.get("category", "Any")
    jtype = cfg.get("type", "single,twopart")
    blacklist = cfg.get("blacklistFlags", [])
    refresh_seconds = float(cfg.get("refresh_seconds", 600))
    timeout = float(cfg.get("request_timeout_seconds", 6))

    api.screen.clear_screen()
    api.screen.write_line("Joke", 0)
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show():
        api.screen.clear_body(start_line=1)
        joke = fetch_joke(category, jtype, blacklist, timeout=timeout)
        if not joke:
            api.screen.write_wrapped("(error/no data)", start_line=2)
            return
        if joke.get("type") == "single":
            api.screen.write_wrapped(joke.get("joke", "No joke."), start_line=2)
        elif joke.get("type") == "twopart":
            setup = joke.get("setup", "No setup")
            delivery = joke.get("delivery", "No punchline")
            api.screen.write_wrapped(setup, start_line=2, max_lines=4)
            # wait for button or refresh interval or stop
            waited = 0.0
            while waited < 30 and not stop_event.is_set():
                if api.hardware.any_button_pressed():  # assuming helper
                    break
                time.sleep(0.25)
                waited += 0.25
            api.screen.clear_body(start_line=1)
            api.screen.write_wrapped(delivery, start_line=2, max_lines=4)
        else:
            api.screen.write_wrapped("No joke.", start_line=2)

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
            time.sleep(0.25)
    finally:
        for sid in sub_ids:
            api.event_bus.unsubscribe(sid)
        api.hardware.set_led("green", False)
        api.screen.clear_screen()
