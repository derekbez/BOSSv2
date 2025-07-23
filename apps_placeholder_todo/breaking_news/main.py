"""
Breaking News Mini-App
Displays global or regional breaking news headlines using NewsData.io or GNews API.
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import requests

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Breaking News mini-app.
    Fetches and displays news headlines from NewsData.io or GNews.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    config = api.get_app_config(default={"api_key": "YOUR_API_KEY_HERE", "country": "gb", "category": "technology"})
    url = "https://newsdata.io/api/1/news"
    params = {
        "apikey": config["api_key"],
        "country": config["country"],
        "category": config["category"]
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        articles = data.get("results", [])
        lines = [f"{a.get('title', '?')} ({a.get('source_id', '')})" for a in articles[:5]]
        text = "\n".join(lines) if lines else "No news found."
    except Exception as e:
        text = f"Error: {e}"
    api.screen.clear()
    api.screen.display_text(text, align="left")
    stop_event.wait()
