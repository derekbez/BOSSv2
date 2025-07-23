"""
Bird Sightings Near Me Mini-App
Shows recent bird species observed in a user-defined area using eBird API.
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import requests

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Bird Sightings Near Me mini-app.
    Fetches and displays recent bird species from eBird API.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    config = api.get_app_config(default={"api_key": "YOUR_API_KEY_HERE", "latitude": 51.5074, "longitude": -0.1278, "radius": 10})
    url = f"https://api.ebird.org/v2/data/obs/geo/recent"
    params = {
        "lat": config["latitude"],
        "lng": config["longitude"],
        "dist": config["radius"]
    }
    headers = {"X-eBirdApiToken": config["api_key"]}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        lines = [f"{b.get('comName', '?')} ({b.get('howMany', '?')}) {b.get('locName', '?')}" for b in data[:5]]
        text = "\n".join(lines) if lines else "No sightings found."
    except Exception as e:
        text = f"Error: {e}"
    api.screen.clear()
    api.screen.display_text(text, align="left")
    stop_event.wait()
