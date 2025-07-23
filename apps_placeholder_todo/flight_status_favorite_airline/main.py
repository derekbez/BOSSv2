"""
Flight Status for Favourite Airline Mini-App
Shows the live status of flights for a user-specified airline using Aviationstack API.
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import requests

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Flight Status for Favourite Airline mini-app.
    Fetches and displays live flight status for a user-specified airline from Aviationstack API.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    config = api.get_app_config(default={"api_key": "YOUR_API_KEY_HERE", "iata": "BA"})
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        "access_key": config["api_key"],
        "airline_iata": config["iata"],
        "limit": 5
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        flights = data.get("data", [])
        lines = [f"{f.get('flight', {}).get('iata', '?')} {f.get('departure', {}).get('scheduled', '')} {f.get('flight_status', '?')}" for f in flights]
        text = "\n".join(lines) if lines else "No flights found."
    except Exception as e:
        text = f"Error: {e}"
    api.screen.clear()
    api.screen.display_text(text, align="left")
    stop_event.wait()
