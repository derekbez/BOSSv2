"""app_jokes - Static joke display with button cycling.

Migration reference mini-app.
"""
from __future__ import annotations
import json
import random
from typing import Any, List
from threading import Event


def run(stop_event: Event, api: Any) -> None:
    api.log_info("app_jokes starting")
    subs: List[int] = []
    jokes: List[str] = []
    idx = 0

    def load_jokes() -> None:
        nonlocal jokes
        try:
            path = api.get_asset_path("jokes.json")
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            jokes = data.get("jokes", []) or ["(no jokes found)"]
        except Exception as e:
            api.log_error(f"Failed loading jokes: {e}")
            jokes = ["(error loading jokes)"]

    def show_current() -> None:
        if not jokes:
            api.screen.display_text("(no jokes)", align="center")
            return
        joke = jokes[idx % len(jokes)]
        api.screen.clear_screen()
        api.screen.display_text(joke, align="center")
        api.log_info(f"Displayed joke {idx % len(jokes)}")

    def next_joke() -> None:
        nonlocal idx
        idx = (idx + 1) % max(1, len(jokes))
        show_current()

    def on_button(event_type: str, payload: dict) -> None:
        button = payload.get("button") or payload.get("button_id")
        if button == "yellow":
            next_joke()

    # Setup
    load_jokes()
    # Retrieve config with backward compatibility: prefer new helper if available
    shuffle = True
    try:
        if hasattr(api, 'get_config_value'):
            shuffle = api.get_config_value("shuffle", True)
        elif hasattr(api, 'get_app_config'):
            cfg = api.get_app_config(default={})
            shuffle = cfg.get("shuffle", True)
    except Exception:
        pass
    if shuffle:
        random.shuffle(jokes)
    show_current()

    # Advertise Yellow button availability
    try:
        api.hardware.set_led("yellow", True)
    except Exception:
        pass

    subs.append(api.event_bus.subscribe("button_pressed", on_button))

    try:
        while not stop_event.wait(0.5):
            pass  # idle; could add periodic screen saver logic
    finally:
        for sid in subs:
            try:
                api.event_bus.unsubscribe(sid)
            except Exception:
                pass
        for c in ("red", "yellow", "green", "blue"):
            try:
                api.hardware.set_led(c, False)
            except Exception:
                pass
        api.log_info("app_jokes stopping")
