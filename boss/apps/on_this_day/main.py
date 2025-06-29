"""
On This Day in History Mini-App
Provides notable historical events, births, and deaths for today’s date using byabbe.se API.
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import requests
import datetime

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the On This Day in History mini-app.
    Fetches and displays events for today’s date.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    today = datetime.date.today()
    url = f"https://byabbe.se/on-this-day/{today.month}/{today.day}/events.json"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        events = data.get("events", [])
        lines = [f"{e.get('year', '?')}: {e.get('description', '?')[:40]}..." for e in events[:5]]
        text = "\n".join(lines) if lines else "No events found."
    except Exception as e:
        text = f"Error: {e}"
    api.screen.clear()
    api.screen.set_cursor(0)
    for line in lines if isinstance(lines, list) else [text]:
        api.screen.print_line(line, size=28)
    stop_event.wait()
