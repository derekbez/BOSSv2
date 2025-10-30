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
    """Main function for the Random Emoji Combo app."""
    cfg = api.get_app_config() or {}
    shuffle_seconds = float(cfg.get("shuffle_seconds", 15.0))
    
    # Derive assets directory using available API helper
    try:
        asset_dir = os.path.dirname(api.get_asset_path("__dummy__"))
    except Exception:
        asset_dir = os.path.join(os.path.dirname(__file__), "assets")
    emojis = load_emojis(asset_dir)
    
    last_shuffle_time = 0.0

    def shuffle_and_display():
        """Choose 2-5 emojis and display them."""
        nonlocal last_shuffle_time
        selected_emojis = random.sample(emojis, k=random.randint(2, 5))
        display_text = " ".join(selected_emojis)
        
        # Use text API so test harness can capture output
        api.screen.clear_screen()
        api.screen.display_text(f"Emoji Combo\n\n{display_text}", align="center")
        last_shuffle_time = time.time()

    def handle_button_press(event_type, event):
        """Callback for button press events."""
        if event.get("button") == "green":
            shuffle_and_display()

    # Setup
    api.screen.clear_screen()
    api.hardware.set_led("green", True)
    sub_id = api.event_bus.subscribe("button_pressed", handle_button_press)
    
    shuffle_and_display()

    try:
        while not stop_event.is_set():
            if time.time() - last_shuffle_time > shuffle_seconds:
                shuffle_and_display()
            time.sleep(0.5)
    finally:
        # Cleanup
        api.event_bus.unsubscribe(sub_id)
        api.hardware.set_led("green", False)
        api.screen.clear_screen()
