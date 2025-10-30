
"""
Test script for TM1637 7-segment display using BOSS config and GPIO abstraction.
Usage:
    python3 scripts/test_tm1637_display.py
"""
import sys
import time
from pathlib import Path

# Add project root to sys.path for boss imports
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from boss.core.models.config import BossConfig
from boss.hardware import GPIODisplay

CONFIG_PATH = PROJECT_ROOT / "boss" / "config" / "boss_config.json"

def main():
    # Load config
    config = BossConfig.from_file(CONFIG_PATH)
    hardware_config = config.hardware

    # Initialize display
    display = GPIODisplay(hardware_config)
    if not display.initialize():
        print("Failed to initialize TM1637 display.")
        return
    print("TM1637 display initialized.")

    try:
        # Test: count 0-9
        for i in range(10):
            print(f"Displaying: {i}")
            display.show_number(i)
            time.sleep(0.5)
        # Test: show 1234
        display.show_number(1234)
        print("Displaying: 1234")
        time.sleep(1)
        # Test: show text
        display.show_text("AbCd")
        print("Displaying: AbCd")
        time.sleep(1)
        # Test: clear
        display.clear()
        print("Display cleared.")
    finally:
        display.cleanup()
        print("Display cleaned up.")

if __name__ == "__main__":
    main()
