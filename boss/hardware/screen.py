"""
Screen abstraction for B.O.S.S. (with mock for dev)
"""
from typing import Protocol
import pygame
import threading

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

class PygameScreen:
    """
    Pygame implementation of the ScreenInterface for B.O.S.S.
    Provides a window for apps to draw text and graphics using pygame.
    """
    def __init__(self, width=800, height=480, caption="BOSS Display"):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(caption)
        self.font = pygame.font.SysFont(None, 48)
        self.lock = threading.Lock()  # For thread safety
        self.clear()
        self._running = True
        # Start a thread to keep pygame event loop alive
        self._event_thread = threading.Thread(target=self._event_loop, daemon=True)
        self._event_thread.start()

    def _event_loop(self):
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
            pygame.time.wait(50)

    def show_status(self, message: str):
        self.display_text(f"STATUS: {message}", color=(0, 255, 0))

    def show_app_output(self, content: str):
        self.display_text(content, color=(255, 255, 255))

    def clear(self):
        with self.lock:
            self.screen.fill((0, 0, 0))
            pygame.display.flip()

    def display_text(self, text: str, color=(255,255,255), center=True, size=48, **kwargs):
        # Accept 'align' kwarg for compatibility with mini-apps
        align = kwargs.get('align', None)
        if align == 'center':
            center = True
        elif align == 'left':
            center = False
        with self.lock:
            self.screen.fill((0, 0, 0))
            font = pygame.font.SysFont(None, size)
            text_surface = font.render(text, True, color)
            rect = text_surface.get_rect()
            if center:
                rect.center = (self.width // 2, self.height // 2)
            else:
                rect.topleft = (10, 10)
            self.screen.blit(text_surface, rect)
            pygame.display.flip()

    def close(self):
        self._running = False
        pygame.quit()

# In the future, a PillowScreen class can be added here for apps that need Pillow drawing.
