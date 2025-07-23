"""
Moon Phase Mini-App
Shows the current phase of the moon and sunrise/sunset data using ipgeolocation.io API.
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import requests

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Moon Phase mini-app.
    Fetches and displays moon phase and sun data from ipgeolocation.io API.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    config = api.get_app_config(default={"api_key": "YOUR_API_KEY_HERE", "latitude": 51.5074, "longitude": -0.1278})
    url = "https://api.ipgeolocation.io/astronomy"
    params = {
        "apiKey": config["api_key"],
        "lat": config["latitude"],
        "long": config["longitude"]
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        text = f"Moon: {data.get('moon_phase', '?')}\nIllum: {data.get('moon_illumination', '?')}%\nRise: {data.get('moonrise', '?')}\nSet: {data.get('moonset', '?')}"
    except Exception as e:
        text = f"Error: {e}"
    api.screen.clear()
    api.screen.display_text(text, align="center")
    stop_event.wait()
