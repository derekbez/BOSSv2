"""
Quote of the Day Mini-App
Fetches and displays a quote from various sources (They Said So, Quotable, Shakespeare).
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import requests
import random
import time

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Quote of the Day mini-app.
    Rotates between APIs or uses user-selected category.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    config = api.get_app_config(default={"source": "quotable", "category": "motivational"})
    sources = [
        {"name": "quotable", "url": "https://api.quotable.io/random", "auth": False},
        {"name": "theysaidso", "url": "https://quotes.rest/qod", "auth": True},
        {"name": "shakespeare", "url": None, "auth": False}
    ]
    source = config.get("source", "quotable")
    selected = next((s for s in sources if s["name"] == source), sources[0])
    quote = None
    if selected["name"] == "quotable":
        try:
            resp = requests.get(selected["url"], timeout=5)
            resp.raise_for_status()
            data = resp.json()
            quote = f'"{data.get("content", "No quote.")}"\n- {data.get("author", "Unknown")}'
        except Exception as e:
            quote = f"Error: {e}"
    elif selected["name"] == "theysaidso":
        quote = "API key required. See manifest.json."
    elif selected["name"] == "shakespeare":
        quote = "Shakespeare quotes require local data."
    api.screen.clear()
    api.screen.display_text(quote, align="center")
    stop_event.wait()
