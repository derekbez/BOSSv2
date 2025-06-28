#!/usr/bin/env python3
"""
Test script for PillowScreen on HDMI framebuffer (/dev/fb0).
Displays a test message in the center of the screen.
"""
from boss.hardware.pillow_screen import PillowScreen
import time

if __name__ == "__main__":
    screen = PillowScreen()
    try:
        screen.display_text("Hello, BOSS!\nThis is PillowScreen.", color=(255,255,0), size=48, align='center')
        time.sleep(5)
        screen.display_text("Test complete!", color=(0,255,0), size=36, align='center')
        time.sleep(3)
        screen.clear()
    finally:
        screen.close()
