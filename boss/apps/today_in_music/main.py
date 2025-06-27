"""
Today in Music Mini-App
Shares a music-related highlight for today or trending track data using Last.fm API.
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import requests
import datetime
import random

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Today in Music mini-app.
    Fetches and displays a music highlight or trending track from Last.fm API.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    config = api.get_app_config(default={"api_key": "YOUR_API_KEY_HERE", "tag": "rock"})
    url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "tag.gettoptracks",
        "tag": config["tag"],
        "api_key": config["api_key"],
        "format": "json",
        "limit": 1
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        track = data.get("tracks", {}).get("track", [{}])[0]
        text = f"{track.get('artist', {}).get('name', '?')} - {track.get('name', '?')}"
    except Exception as e:
        text = f"Error: {e}"
    api.screen.clear()
    api.screen.display_text(text, align="center")
    stop_event.wait()
