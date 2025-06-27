"""
Flights Leaving Heathrow Mini-App
Displays upcoming departures from Heathrow Airport using Aviationstack API.
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import requests

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Flights Leaving Heathrow mini-app.
    Fetches and displays next 5–10 departures from EGLL using Aviationstack API.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    config = api.get_app_config(default={"api_key": "YOUR_API_KEY_HERE"})
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        "access_key": config["api_key"],
        "dep_iata": "EGLL",
        "limit": 10
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        flights = data.get("data", [])
        lines = [f"{f.get('airline', {}).get('name', '?')} {f.get('flight', {}).get('iata', '')} {f.get('departure', {}).get('scheduled', '')}" for f in flights]
        text = "\n".join(lines) if lines else "No flights found."
    except Exception as e:
        text = f"Error: {e}"
    api.screen.clear()
    api.screen.display_text(text, align="left")
    stop_event.wait()
