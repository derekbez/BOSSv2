"""
Screen abstraction for B.O.S.S. (with mock for dev)
"""
from typing import Protocol

class ScreenInterface(Protocol):
    def show_status(self, message: str):
        ...
    def show_app_output(self, content: str):
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
