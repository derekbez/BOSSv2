#!/usr/bin/env python3
"""
Test script for PillowScreen on HDMI framebuffer (/dev/fb0).
Demonstrates print_line, draw_text, and cursor control.
"""
from boss.hardware.pillow_screen import PillowScreen
import time

if __name__ == "__main__":
    print("[DEBUG] Starting PillowScreen print_line/draw_text test...")
    screen = PillowScreen()  # Use real framebuffer
    try:
        screen.clear()
        # Print several lines with different sizes/colors using print_line
        screen.print_line("Default size (centered)", color=(255,255,255))
        screen.print_line("Largest", color=(255,255,0), size=screen.FONT_SIZE_LARGEST)
        screen.print_line("Larger", color=(0,255,0), size=screen.FONT_SIZE_LARGER)
        screen.print_line("Smaller", color=(0,255,255), size=screen.FONT_SIZE_SMALLER)
        screen.print_line("Smallest", color=(255,0,255), size=screen.FONT_SIZE_SMALLEST)
        screen.print_line("Random size 72", color=(255,0,0), size=72)
        # Draw a line at a specific position
        screen.draw_text(20, 500, "draw_text at (20,500)", color=(255,128,0), size=64)
        # Update framebuffer once at the end
        screen._update_fb()
        print("[DEBUG] All lines drawn. Text should remain on screen.")
        time.sleep(5)
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
        raise
    finally:
        screen.close()
        print("[DEBUG] Screen closed. Exiting.")
