"""
Screen abstraction for B.O.S.S. (with mock for dev)
"""
from typing import Protocol
import threading

def get_screen(*args, **kwargs):
    """
    Factory function to return a real PillowScreen if possible, else a MockScreen.
    Handles all import errors and dependency checks.
    Accepts any args/kwargs for PillowScreen/MockScreen.
    """
    try:
        from boss.hardware.pillow_screen import PillowScreen
        # Check if PillowScreen dependencies are present
        if getattr(PillowScreen, 'FONT_SIZE_DEFAULT', None) is not None:
            screen = PillowScreen(*args, **kwargs)
            # If PillowScreen is in mock mode or missing image, fallback
            if getattr(screen, 'image', None) is not None:
                return screen
    except Exception as e:
        pass
    # Fallback to MockScreen
    return MockScreen(*args, **kwargs)

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
    FONT_SIZE_LARGEST = 64
    FONT_SIZE_LARGER = 48
    FONT_SIZE_DEFAULT = 32
    FONT_SIZE_SMALLER = 24
    FONT_SIZE_SMALLEST = 16

    def __init__(self, event_bus=None, width=1024, height=600, stride=2048, bpp=2, fbdev=None, mock=True):
        self.event_bus = event_bus
        self.width = width
        self.height = height
        self.stride = stride
        self.bpp = bpp
        self.fbdev = fbdev
        self.mock = mock
        self.cursor_y = 0
        self.lines = []
        self.last_output = None
        self.last_status = None
        self.image = None
        self.draw = None
        self.font = None

    def clear(self, color=(0,0,0)):
        self.last_status = None
        self.last_output = None
        self.lines = []
        self.cursor_y = 0
        print("[MOCK SCREEN] CLEARED")
        if self.event_bus:
            self.event_bus.publish(
                "output.screen.updated",
                {
                    "action": "clear",
                    "details": {"text": ""},
                    "timestamp": time.time(),
                    "source": "hardware.screen.mock"
                }
            )

    def display_text(self, text, color=(255,255,255), size=32, align='center', font_name=None):
        self.last_output = text
        print(f"[MOCK SCREEN] DISPLAY: {text}")
        if self.event_bus:
            details = {"text": text, "color": color, "size": size, "align": align, "font_name": font_name}
            self.event_bus.publish(
                "output.screen.updated",
                {
                    "action": "display_text",
                    "details": details,
                    "timestamp": time.time(),
                    "source": "hardware.screen.mock"
                }
            )

    def print_line(self, text, color=(255,255,255), size=None, font_name=None, x=None, spacing=10, align='left'):
        print(f"[MOCK SCREEN] PRINT_LINE: {text} (align={align})")
        self.lines.append(text)
        self.cursor_y += 1
        # Publish the full screen content (all lines joined by newlines)
        if self.event_bus:
            full_content = "\n".join(self.lines)
            details = {"text": full_content, "color": color, "size": size, "align": align, "font_name": font_name, "x": x, "spacing": spacing}
            self.event_bus.publish(
                "output.screen.updated",
                {
                    "action": "print_line",
                    "details": details,
                    "timestamp": time.time(),
                    "source": "hardware.screen.mock"
                }
            )

    def draw_text(self, x, y, text, color=(255,255,255), size=None, font_name=None):
        print(f"[MOCK SCREEN] DRAW_TEXT at ({x},{y}): {text}")
        if self.event_bus:
            details = {"x": x, "y": y, "text": text, "color": color, "size": size, "font_name": font_name}
            self.event_bus.publish(
                "output.screen.updated",
                {
                    "action": "draw_text",
                    "details": details,
                    "timestamp": time.time(),
                    "source": "hardware.screen.mock"
                }
            )

    def set_cursor(self, y=0):
        self.cursor_y = y
        print(f"[MOCK SCREEN] SET_CURSOR: {y}")
        if self.event_bus:
            self.event_bus.publish(
                "output.screen.updated",
                {
                    "action": "set_cursor",
                    "details": {"y": y},
                    "timestamp": time.time(),
                    "source": "hardware.screen.mock"
                }
            )

    def reset_cursor(self):
        self.cursor_y = 0
        print("[MOCK SCREEN] RESET_CURSOR")
        if self.event_bus:
            self.event_bus.publish(
                "output.screen.updated",
                {
                    "action": "reset_cursor",
                    "details": {},
                    "timestamp": time.time(),
                    "source": "hardware.screen.mock"
                }
            )

    def refresh(self):
        print("[MOCK SCREEN] REFRESH (would update framebuffer in real screen)")
        if self.event_bus:
            self.event_bus.publish(
                "output.screen.updated",
                {
                    "action": "refresh",
                    "details": {},
                    "timestamp": time.time(),
                    "source": "hardware.screen.mock"
                }
            )

    def display_image(self, img):
        print(f"[MOCK SCREEN] DISPLAY_IMAGE: {img}")
        if self.event_bus:
            self.event_bus.publish(
                "output.screen.updated",
                {
                    "action": "display_image",
                    "details": {"img": str(img)},
                    "timestamp": time.time(),
                    "source": "hardware.screen.mock"
                }
            )

    def save_to_file(self, path):
        print(f"[MOCK SCREEN] SAVE_TO_FILE: {path}")
        if self.event_bus:
            self.event_bus.publish(
                "output.screen.updated",
                {
                    "action": "save_to_file",
                    "details": {"path": path},
                    "timestamp": time.time(),
                    "source": "hardware.screen.mock"
                }
            )

    def close(self):
        print("[MOCK SCREEN] CLOSE")
        if self.event_bus:
            self.event_bus.publish(
                "output.screen.updated",
                {
                    "action": "close",
                    "details": {},
                    "timestamp": time.time(),
                    "source": "hardware.screen.mock"
                }
            )

    # For compatibility with PillowScreen
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

