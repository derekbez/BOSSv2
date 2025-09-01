"""Random Emoji Combo mini-app.

Chooses 2-5 emojis from an asset list and displays them. Auto shuffle interval or button.
"""
from __future__ import annotations
import json
import os
import random
import time

ASSET_FILE = "emoji.json"


def load_emojis(asset_dir: str):
    path = os.path.join(asset_dir, ASSET_FILE)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return ["😀", "🚀", "🌍", "🐍", "✨"]


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    min_n = int(cfg.get("min", 2))
    max_n = int(cfg.get("max", 5))
    shuffle_seconds = float(cfg.get("shuffle_seconds", 30))

    asset_dir = api.get_app_asset_path()
    emojis = load_emojis(asset_dir)

    api.screen.clear_screen()
    title = "Emoji Combo"
    def on_button(event_type, payload):
    api.hardware.set_led("green", True)
        if payload.get("button") == "green":
    sub_ids = []
    last_shuffle = 0.0

    def show():
        n = random.randint(min_n, max_n)
        combo = "".join(random.sample(emojis, k=min(len(emojis), n)))
        api.screen.display_text(f"{title}\n\n{combo}", align="center")

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
