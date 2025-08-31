"""Joke of the Moment mini-app.

Fetches a joke from JokeAPI. For two-part jokes, waits for a button before punchline.
Refreshes periodically or via button.
"""
from __future__ import annotations
import time
from textwrap import shorten

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
    title = "Joke"
    api.screen.display_text(title, font_size=26, align="center")
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    punchline_state = {"pending": False, "delivery": ""}

    def show():
        joke = fetch_joke(category, jtype, blacklist, timeout=timeout)
        if not joke:
            api.screen.display_text(f"{title}\n\n(error/no data)", align="left")
            punchline_state["pending"] = False
            return
        jtype_local = joke.get("type")
        if jtype_local == "single":
            text = shorten(joke.get("joke", "No joke."), width=240, placeholder="…")
            api.screen.display_text(f"{title}\n\n{text}", align="left")
            punchline_state["pending"] = False
        elif jtype_local == "twopart":
            setup = shorten(joke.get("setup", "No setup"), width=220, placeholder="…")
            delivery = shorten(joke.get("delivery", "No punchline"), width=220, placeholder="…")
            punchline_state["pending"] = True
            punchline_state["delivery"] = delivery
            api.screen.display_text(f"{title}\n\n{setup}\n\n(press green)", align="left")
        else:
            api.screen.display_text(f"{title}\n\nNo joke.", align="left")
            punchline_state["pending"] = False

    def on_button(ev):
        nonlocal last_fetch
        if ev.get("button") == "green":
            if punchline_state["pending"]:
                punchline_state["pending"] = False
                api.screen.display_text(f"{title}\n\n{punchline_state['delivery']}", align="left")
            else:
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
