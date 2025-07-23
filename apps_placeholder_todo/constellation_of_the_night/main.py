"""
Constellation of the Night Mini-App
Displays a featured constellation based on the user's location and time using Stellarium data or web scraping.
Implements the B.O.S.S. app API contract.
"""
import threading
from typing import Any
# import requests  # For future web scraping or API

def run(stop_event: threading.Event, api: Any) -> None:
    """
    Entry point for the Constellation of the Night mini-app.
    (Stub) Displays a placeholder constellation. Real implementation may require local Stellarium data or scraping.
    Args:
        stop_event: threading.Event to signal app termination
        api: Provided API object for hardware/screen access
    """
    # TODO: Implement real constellation lookup using coordinates and time
    text = "Orion\nVisible tonight!\n(More info in future)"
    api.screen.clear()
    api.screen.display_text(text, align="center")
    stop_event.wait()
