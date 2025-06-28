"""
Mini-app: Admin Wi-Fi Configuration
Provides UI and web server for Wi-Fi setup via AP mode.
Entry point: run(stop_event, api)
"""
from threading import Event
from typing import Any

def run(stop_event: Event, api: Any) -> None:
    """
    Starts AP mode, web server, and handles Wi-Fi credential collection.
    Args:
        stop_event (Event): Event to signal app termination.
        api (object): Provided API for hardware/display access.
    """
    # TODO: Implement AP mode, web server, and credential handling
    pass
