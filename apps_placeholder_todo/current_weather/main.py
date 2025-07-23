"""
Current Weather Mini-App
Displays real-time weather for the user's preset or geolocated location.
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import requests

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Current Weather mini-app.
    Fetches and displays weather data from Open-Meteo.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    config = api.get_app_config(default={"latitude": 51.5074, "longitude": -0.1278})
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": config["latitude"],
        "longitude": config["longitude"],
        "current_weather": True
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        weather = data.get("current_weather", {})
        text = f"Temp: {weather.get('temperature', '?')}°C\nWind: {weather.get('windspeed', '?')} km/h\nCloud: {weather.get('cloudcover', '?')}%"
    except Exception as e:
        text = f"Error: {e}"
    api.screen.clear()
    api.screen.display_text(text, align="center")
    stop_event.wait()
