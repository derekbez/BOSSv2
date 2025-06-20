import json
import os
import random

def run(stop_event, api):
    """
    Mini-app entry point. Displays a random joke from jokes.json on the 7-inch screen.
    Args:
        stop_event: threading.Event to signal app termination
        api: object with .screen (7-inch display) interface
    """
    # Locate jokes.json in the assets folder
    assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
    jokes_path = os.path.join(assets_dir, 'jokes.json')
    with open(jokes_path, 'r') as f:
        jokes = json.load(f)["jokes"]
    joke = random.choice(jokes)
    # Display the joke centered on the screen
    api.screen.clear()
    api.screen.display_text(joke, align='center')
    # Wait until stop_event is set (app terminated)
    stop_event.wait()
