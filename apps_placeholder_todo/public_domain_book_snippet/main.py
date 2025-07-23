"""
Public Domain Book Snippet Mini-App
Displays a short passage from classic literature in the public domain (Gutenberg).
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
import random
import os

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Public Domain Book Snippet mini-app.
    Loads a random snippet from a local text file in assets/.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
    try:
        books = [f for f in os.listdir(assets_dir) if f.endswith('.txt')]
        if not books:
            raise FileNotFoundError('No book files found in assets/')
        book_path = os.path.join(assets_dir, random.choice(books))
        with open(book_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        snippet = ''.join(random.sample(lines, k=min(5, len(lines))))
    except Exception as e:
        snippet = f"Error: {e}"
    api.screen.clear()
    api.screen.set_cursor(0)
    for line in snippet.splitlines():
        api.screen.print_line(line, size=28)
    stop_event.wait()
