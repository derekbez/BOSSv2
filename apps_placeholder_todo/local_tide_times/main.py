"""
Local Tide Times Mini-App
Provides tide predictions for the user's local coast or harbor using WorldTides API.
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import requests

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Local Tide Times mini-app.
    Fetches and displays next high and low tides from WorldTides API.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    config = api.get_app_config(default={"api_key": "YOUR_API_KEY_HERE", "latitude": 51.5074, "longitude": -0.1278})
    url = "https://www.worldtides.info/api"
    params = {
        "key": config["api_key"],
        "lat": config["latitude"],
        "lon": config["longitude"],
        "extremes": ""
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        tides = data.get("extremes", [])
        lines = [f"{t.get('date', '?')} {t.get('type', '?')}" for t in tides[:2]]
        text = "\n".join(lines) if lines else "No tide data."
    except Exception as e:
        text = f"Error: {e}"
    api.screen.clear()
    api.screen.display_text(text, align="center")
    stop_event.wait()
