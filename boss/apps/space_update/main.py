"""
Space Update Mini-App
Displays astronomy content such as NASA's Astronomy Picture of the Day or Mars rover photos using NASA API.
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import requests
import random

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Space Update mini-app.
    Fetches and displays astronomy content from NASA API.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    config = api.get_app_config(default={"api_key": "DEMO_KEY"})
    endpoints = [
        ("apod", "https://api.nasa.gov/planetary/apod"),
        ("mars", "https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos")
    ]
    name, url = random.choice(endpoints)
    params = {"api_key": config["api_key"]}
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if name == "apod":
            text = data.get("title", "No title.") + "\n" + data.get("explanation", "No summary.")[:60] + "..."
        else:
            photos = data.get("photos", [])
            text = photos[0].get("earth_date", "No photo.") if photos else "No Mars photos."
    except Exception as e:
        text = f"Error: {e}"
    api.screen.clear()
    api.screen.display_text(text, align="center")
    stop_event.wait()
