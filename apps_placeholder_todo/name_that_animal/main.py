"""
Name That Animal Mini-App
Presents a random animal's name, facts, and image using Zoo Animal API.
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import requests

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Name That Animal mini-app.
    Fetches and displays a random animal's name, image, and facts from Zoo Animal API.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    url = "https://zoo-animal-api.herokuapp.com/animals/rand"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        name = data.get("name", "?")
        fact = data.get("diet", "No fact.")
        text = f"{name}\n{fact}"
    except Exception as e:
        text = f"Error: {e}"
    api.screen.clear()
    api.screen.display_text(text, align="center")
    stop_event.wait()
