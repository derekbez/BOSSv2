"""
Dad Joke Generator Mini-App
Fetches a groan-worthy one-liner from the official Dad Joke API.
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import requests

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Dad Joke Generator mini-app.
    Fetches and displays a dad joke from icanhazdadjoke.com.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    url = "https://icanhazdadjoke.com/"
    headers = {"Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        joke = data.get("joke", "No joke found.")
    except Exception as e:
        joke = f"Error: {e}"
    api.screen.clear()
    api.screen.display_text(joke, align="center")
    stop_event.wait()
