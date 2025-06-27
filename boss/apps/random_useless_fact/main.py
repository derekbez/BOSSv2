"""
Random Useless Fact Mini-App
Displays an amusing and often bizarre fact using Useless Facts API.
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import requests

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Random Useless Fact mini-app.
    Fetches and displays a random fact from Useless Facts API.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    url = "https://uselessfacts.jsph.pl/random.json?language=en"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        text = data.get("text", "No fact found.")
    except Exception as e:
        text = f"Error: {e}"
    api.screen.clear()
    api.screen.display_text(text, align="center")
    stop_event.wait()
