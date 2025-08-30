"""Random Local Place Name mini-app.

Selects a name from local assets/places.json.
"""
from __future__ import annotations
import json
import os
import random
import time

ASSET_FILE = "places.json"


def load_places(asset_dir: str):
    path = os.path.join(asset_dir, ASSET_FILE)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return ["Sampleville", "Widgettown", "Fooville", "Bar City"]


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    shuffle_seconds = float(cfg.get("shuffle_seconds", 300))

    places = load_places(api.get_app_asset_path())

    api.screen.clear_screen()
    api.screen.write_line("Place Name", 0)
    api.hardware.set_led("green", True)

    sub_ids = []
    last_shuffle = 0.0

    def show():
        api.screen.clear_body(start_line=1)
        place = random.choice(places)
        api.screen.write_line(place[: api.screen.width - 1], 2)

    def on_button(ev):
        nonlocal last_shuffle
        if ev.get("button") == "green":
            last_shuffle = time.time()
            show()

    sub_ids.append(api.event_bus.subscribe("button_pressed", on_button))

    try:
        show()
        last_shuffle = time.time()
        while not stop_event.is_set():
            if time.time() - last_shuffle >= shuffle_seconds:
                last_shuffle = time.time()
                show()
            time.sleep(0.5)
    finally:
        for sid in sub_ids:
            api.event_bus.unsubscribe(sid)
        api.hardware.set_led("green", False)
        api.screen.clear_screen()
