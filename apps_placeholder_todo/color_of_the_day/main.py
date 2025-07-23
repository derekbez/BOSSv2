"""
Color of the Day Mini-App
Selects a daily color and displays its name, hex code, and palette inspiration using ColourLovers API.
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import requests
import xml.etree.ElementTree as ET


def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Color of the Day mini-app.
    Fetches and displays a random color from ColourLovers API.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    url = "https://www.colourlovers.com/api/colors/random?format=xml"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        color = root.find('color')
        name = color.find('title').text if color is not None else '?'
        hexcode = color.find('hex').text if color is not None else '?'
        text = f"{name}\n#{hexcode}"
    except Exception as e:
        text = f"Error: {e}"
    api.screen.clear()
    api.screen.display_text(text, align="center")
    stop_event.wait()
