"""Public Domain Book Snippet mini-app.

Selects N random lines from a random text file in assets.
"""
from __future__ import annotations
import os
import random
import time
from textwrap import shorten


def choose_snippet(asset_dir: str, lines: int):
    try:
        books = [f for f in os.listdir(asset_dir) if f.endswith('.txt')]
        if not books:
            return ["(no book files)"]
        path = os.path.join(asset_dir, random.choice(books))
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = [l.rstrip() for l in f.readlines() if l.strip()]
        if not all_lines:
            return ["(empty book file)"]
        sample = random.sample(all_lines, k=min(lines, len(all_lines)))
        return sample
    except Exception as e:
        return [f"Error: {e}"]


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    lines = int(cfg.get("lines", 5))
    shuffle_seconds = float(cfg.get("shuffle_seconds", 600))

    asset_dir = api.get_app_asset_path()

    api.screen.clear_screen()
    title = "Book Snippet"
    api.screen.display_text(title, font_size=24, align="center")
    api.hardware.set_led("green", True)

    sub_ids = []
    last_shuffle = 0.0

    def show():
        snippet_lines = choose_snippet(asset_dir, lines)
        body = "\n".join(shorten(line, width=80, placeholder="…") for line in snippet_lines[:10])
        api.screen.display_text(f"{title}\n\n{body}", align="left")

    def on_button(event_type: str, payload: dict):
        nonlocal last_shuffle
        if payload.get("button") == "green":
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
