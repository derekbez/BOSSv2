"""
Screen abstraction for B.O.S.S. (with mock for dev)
"""
from typing import Protocol

class ScreenInterface(Protocol):
    def show_status(self, message: str):
        ...
    def show_app_output(self, content: str):
        ...
    def clear(self):
        ...
    def display_text(self, text: str):
        ...

class MockScreen:
    def __init__(self):
        self.last_status = None
        self.last_output = None
    def show_status(self, message: str):
        self.last_status = message
        print(f"[MOCK SCREEN] STATUS: {message}")
    def show_app_output(self, content: str):
        self.last_output = content
        print(f"[MOCK SCREEN] APP OUTPUT: {content}")
    def clear(self):
        # Clear the mock screen output
        self.last_status = None
        self.last_output = None
        print("[MOCK SCREEN] CLEARED")
    def display_text(self, text: str, **kwargs):
        # Display arbitrary text on the mock screen, ignore extra kwargs
        self.last_output = text
        print(f"[MOCK SCREEN] DISPLAY: {text}")

class PiScreen:
    """
    Real hardware implementation of the ScreenInterface for B.O.S.S.
    Replace the methods below with actual hardware display logic as needed.
    """
    def __init__(self):
        # Initialize hardware display here (e.g., I2C/SPI LCD, OLED, etc.)
        pass

    def show_status(self, message: str):
        # Display status message on the real hardware screen
        print(f"[PI SCREEN] STATUS: {message}")  # Replace with real display logic

    def show_app_output(self, content: str):
        # Display app output on the real hardware screen
        print(f"[PI SCREEN] APP OUTPUT: {content}")  # Replace with real display logic

    def clear(self):
        # Clear the real hardware screen (replace with actual logic)
        print("[PI SCREEN] CLEARED")

    def display_text(self, text: str, **kwargs):
        # Display arbitrary text on the real hardware screen, ignore extra kwargs
        print(f"[PI SCREEN] DISPLAY: {text}")
