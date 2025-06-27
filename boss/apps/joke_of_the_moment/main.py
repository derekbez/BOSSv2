"""
Joke of the Moment Mini-App
Displays a random joke from JokeAPI (https://v2.jokeapi.dev/).
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import requests
import random
import time


def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Joke of the Moment mini-app.
    Fetches and displays a random joke from JokeAPI.
    Handles both single and two-part joke formats.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    config = api.get_app_config(default={"category": "Any", "type": "single,two-part", "blacklistFlags": ["nsfw", "religious", "political", "racist", "sexist"]})
    base_url = "https://v2.jokeapi.dev/joke/"
    category = config.get("category", "Any")
    joke_type = config.get("type", "single,two-part")
    blacklist = config.get("blacklistFlags", [])
    params = {
        "type": joke_type,
        "blacklistFlags": ",".join(blacklist)
    }
    url = f"{base_url}{category}"
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        joke = resp.json()
    except Exception as e:
        api.screen.display_text(f"Error: {e}", align="center")
        stop_event.wait()
        return
    api.screen.clear()
    if joke.get("type") == "single":
        api.screen.display_text(joke.get("joke", "No joke found."), align="center")
        stop_event.wait()
    elif joke.get("type") == "twopart":
        api.screen.display_text(joke.get("setup", "No setup."), align="center")
        # Wait for button press or stop_event
        while not stop_event.is_set():
            if api.buttons.any_pressed():
                break
            time.sleep(0.1)
        api.screen.clear()
        api.screen.display_text(joke.get("delivery", "No punchline."), align="center")
        stop_event.wait()
    else:
        api.screen.display_text("No joke found.", align="center")
        stop_event.wait()
