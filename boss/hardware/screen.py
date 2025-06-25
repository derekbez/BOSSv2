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
        """
        Display arbitrary text on the mock screen, print all advanced options for dev/test.
        """
        self.last_output = text
        print(f"[MOCK SCREEN] DISPLAY: {text}")
        if kwargs:
            print(f"[MOCK SCREEN] OPTIONS: {kwargs}")

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
        """
        Display arbitrary text on the real hardware screen, print all advanced options for now.
        """
        print(f"[PI SCREEN] DISPLAY: {text}")
        if kwargs:
            print(f"[PI SCREEN] OPTIONS: {kwargs}")

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
        """
        Display text with advanced options:
        - color: (r,g,b) tuple
        - center: bool (centered if True)
        - size: font size
        - x, y: position (overrides center)
        - font_name: font family
        - bg_color: background color
        - bold, italic, underline: text effects
        - shadow: (offset, color)
        - align: 'center', 'left', 'right'
        - multiline: bool (split on \n)
        - wrap: int (max width in px)
        - opacity: 0-255
        - outline: (color, thickness)
        - emoji: bool (default True)
        """
        align = kwargs.get('align', None)
        if align == 'center':
            center = True
        elif align == 'left':
            center = False
        x = kwargs.get('x', None)
        y = kwargs.get('y', None)
        font_name = kwargs.get('font_name', None)
        bg_color = kwargs.get('bg_color', (0,0,0))
        bold = kwargs.get('bold', False)
        italic = kwargs.get('italic', False)
        underline = kwargs.get('underline', False)
        shadow = kwargs.get('shadow', None)  # (offset, color)
        multiline = kwargs.get('multiline', True)
        wrap = kwargs.get('wrap', None)
        opacity = kwargs.get('opacity', 255)
        outline = kwargs.get('outline', None)  # (color, thickness)
        # emoji = kwargs.get('emoji', True)  # Pygame supports Unicode, emoji if font does
        text_lines = [text]
        if multiline:
            text_lines = text.split('\n')
        with self.lock:
            self.screen.fill(bg_color)
            font = pygame.font.SysFont(font_name, size, bold=bold, italic=italic)
            font.set_underline(underline)
            y_offset = 0
            for line in text_lines:
                # Word wrap if needed
                if wrap:
                    words = line.split(' ')
                    line_buf = ''
                    for word in words:
                        test_line = (line_buf + ' ' + word).strip()
                        test_surface = font.render(test_line, True, color)
                        if test_surface.get_width() > wrap:
                            # Draw current line_buf
                            self._draw_text(font, line_buf, color, bg_color, x, y, center, y_offset, shadow, opacity, outline)
                            y_offset += test_surface.get_height()
                            line_buf = word
                        else:
                            line_buf = test_line
                    if line_buf:
                        self._draw_text(font, line_buf, color, bg_color, x, y, center, y_offset, shadow, opacity, outline)
                        y_offset += font.get_height()
                else:
                    self._draw_text(font, line, color, bg_color, x, y, center, y_offset, shadow, opacity, outline)
                    y_offset += font.get_height()
            pygame.display.flip()

    def _draw_text(self, font, text, color, bg_color, x, y, center, y_offset, shadow, opacity, outline):
        # Render text with effects
        text_surface = font.render(text, True, color)
        if opacity < 255:
            text_surface.set_alpha(opacity)
        rect = text_surface.get_rect()
        # Positioning
        if x is not None and y is not None:
            rect.topleft = (x, y + y_offset)
        elif center:
            rect.center = (self.width // 2, self.height // 2 + y_offset)
        else:
            rect.topleft = (10, 10 + y_offset)
        # Shadow
        if shadow:
            offset, shadow_color = shadow
            shadow_surface = font.render(text, True, shadow_color)
            shadow_rect = rect.copy()
            shadow_rect.x += offset[0]
            shadow_rect.y += offset[1]
            self.screen.blit(shadow_surface, shadow_rect)
        # Outline
        if outline:
            outline_color, thickness = outline
            for dx in range(-thickness, thickness+1):
                for dy in range(-thickness, thickness+1):
                    if dx == 0 and dy == 0:
                        continue
                    outline_surface = font.render(text, True, outline_color)
                    outline_rect = rect.copy()
                    outline_rect.x += dx
                    outline_rect.y += dy
                    self.screen.blit(outline_surface, outline_rect)
        # Main text
        self.screen.blit(text_surface, rect)

    def close(self):
        self._running = False
        pygame.quit()

# In the future, a PillowScreen class can be added here for apps that need Pillow drawing.
