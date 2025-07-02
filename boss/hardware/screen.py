"""
Screen abstraction for B.O.S.S. (with mock for dev)
"""
from typing import Protocol
import threading
from boss.hardware.pillow_screen import PillowScreen

class ScreenInterface(Protocol):
    def show_status(self, message: str):
        ...
    def show_app_output(self, content: str):
        ...
    def clear(self):
        ...
    def display_text(self, text: str):
        ...


import time

class MockScreen:
    def __init__(self, event_bus=None):
        self.last_status = None
        self.last_output = None
        self.event_bus = event_bus
    def show_status(self, message: str):
        self.last_status = message
        print(f"[MOCK SCREEN] STATUS: {message}")
        if self.event_bus:
            self.event_bus.publish(
                "output.screen.updated",
                {
                    "action": "show_status",
                    "details": {"text": message},
                    "timestamp": time.time(),
                    "source": "hardware.screen.mock"
                }
            )
    def show_app_output(self, content: str):
        self.last_output = content
        print(f"[MOCK SCREEN] APP OUTPUT: {content}")
        if self.event_bus:
            self.event_bus.publish(
                "output.screen.updated",
                {
                    "action": "show_app_output",
                    "details": {"text": content},
                    "timestamp": time.time(),
                    "source": "hardware.screen.mock"
                }
            )
    def clear(self):
        # Clear the mock screen output
        self.last_status = None
        self.last_output = None
        print("[MOCK SCREEN] CLEARED")
        if self.event_bus:
            self.event_bus.publish(
                "output.screen.updated",
                {
                    "action": "clear",
                    "timestamp": time.time(),
                    "source": "hardware.screen.mock"
                }
            )
    def display_text(self, text: str, **kwargs):
        """
        Display arbitrary text on the mock screen, print all advanced options for dev/test.
        """
        self.last_output = text
        print(f"[MOCK SCREEN] DISPLAY: {text}")
        if kwargs:
            print(f"[MOCK SCREEN] OPTIONS: {kwargs}")
        if self.event_bus:
            details = {"text": text}
            details.update(kwargs)
            self.event_bus.publish(
                "output.screen.updated",
                {
                    "action": "display_text",
                    "details": details,
                    "timestamp": time.time(),
                    "source": "hardware.screen.mock"
                }
            )

