"""
Random Emoji Combo Mini-App
Displays a whimsical sequence of emojis loaded from a static emoji table.
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import random
import json
import os

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Random Emoji Combo mini-app.
    Loads emoji table from assets and displays 2–5 random emojis.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
    emoji_path = os.path.join(assets_dir, 'emoji.json')
    try:
        with open(emoji_path, 'r', encoding='utf-8') as f:
            emojis = json.load(f)
        combo = ''.join(random.sample(emojis, k=random.randint(2, 5)))
    except Exception as e:
        combo = f"Error: {e}"
    api.screen.clear()
    api.screen.display_text(combo, align="center")
    stop_event.wait()
