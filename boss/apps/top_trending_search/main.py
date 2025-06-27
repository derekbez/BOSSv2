"""
Top Trending Search Mini-App
Displays the top search trend for the current day using Google Trends data (unofficial Node.js backend required).
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import requests

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Top Trending Search mini-app.
    Fetches and displays the top trending search keyword from a local Node.js backend.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    # This app expects a local Node.js backend to provide the trending keyword as JSON
    url = "http://localhost:3000/toptrends"  # Example endpoint
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        trend = data.get("trend", "No trend found.")
    except Exception as e:
        trend = f"Error: {e}"
    api.screen.clear()
    api.screen.display_text(trend, align="center")
    stop_event.wait()
