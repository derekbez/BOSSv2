"""
Tiny Poem or Haiku Mini-App
Displays a short poem from Poemist API.
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import requests

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Tiny Poem or Haiku mini-app.
    Fetches and displays a random poem from Poemist API.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    url = "https://www.poemist.com/api/v1/randompoems"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        poem = data[0] if data else {}
        text = f"{poem.get('title', '?')}\n{poem.get('content', '?')[:60]}...\n- {poem.get('poet', {}).get('name', '?')}"
    except Exception as e:
        text = f"Error: {e}"
    api.screen.clear()
    api.screen.display_text(text, align="center")
    stop_event.wait()
