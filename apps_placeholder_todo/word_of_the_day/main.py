"""
Word of the Day Mini-App
Displays a new English word, its definition, pronunciation, and usage using Wordnik API.
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import requests

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Word of the Day mini-app.
    Fetches and displays the word of the day from Wordnik API.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    config = api.get_app_config(default={"api_key": "YOUR_API_KEY_HERE"})
    url = "https://api.wordnik.com/v4/words.json/wordOfTheDay"
    params = {"api_key": config["api_key"]}
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        word = data.get("word", "?")
        defs = data.get("definitions", [{}])[0].get("text", "No definition.")
        example = data.get("examples", [{}])[0].get("text", "")
        text = f"{word}: {defs}\nEx: {example}"
    except Exception as e:
        text = f"Error: {e}"
    api.screen.clear()
    api.screen.display_text(text, align="center")
    stop_event.wait()
