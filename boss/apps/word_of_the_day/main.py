"""Word of the Day mini-app.

Uses Wordnik API. Refresh infrequently (half-day) or manually.
"""
from __future__ import annotations
import time
from textwrap import shorten

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

API_URL = "https://api.wordnik.com/v4/words.json/wordOfTheDay"


def fetch_word(api_key: str | None, timeout: float = 6.0):
    if requests is None:
        return None
    params = {}
    if api_key:
        params["api_key"] = api_key
    try:
        r = requests.get(API_URL, params=params, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            word = data.get("word") or "?"
            defs = data.get("definitions", [{}])[0].get("text", "No definition.")
            example = data.get("examples", [{}])[0].get("text", "")
            return word, defs, example
    except Exception:
        return None
    return None


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    api_key = cfg.get("api_key") or api.get_config_value("WORDNIK_API_KEY")
    refresh_seconds = float(cfg.get("refresh_seconds", 43200))
    timeout = float(cfg.get("request_timeout_seconds", 6))

    api.screen.clear_screen()
    title = "Word of the Day"
    api.screen.display_text(title, font_size=28, align="center")
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show():
        result = fetch_word(api_key, timeout=timeout)
        if not result:
            api.screen.display_text(f"{title}\n\n(error/ no data)", align="left")
            return
        word, defs, example = result
        defs_txt = shorten(defs, width=200, placeholder="…")
        lines = [title, "", word, defs_txt]
        if example:
            lines.append("")
            lines.append("Ex: " + shorten(example, width=160, placeholder="…"))
        api.screen.display_text("\n".join(lines), align="left")

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
