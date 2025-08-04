#!/usr/bin/env python3
"""
Quick test to verify LED blinking works in WebUI
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from boss.main import create_boss_system
import time
import threading

def test_led_blinking():
    """Test LED blinking functionality"""
    print("Creating BOSS system...")
    system_manager, config = create_boss_system()
    
    print("Starting BOSS system...")
    system_manager.start()
    
    # Wait a moment for system to fully initialize
    time.sleep(2)
    
    try:
        print("Testing LED blinking sequence...")
        hardware_service = system_manager.hardware_service
        
        colors = ["red", "yellow", "green", "blue"]
        
        for cycle in range(2):
            print(f"Blink cycle {cycle + 1}/2")
            for color in colors:
                print(f"  Turning ON {color} LED")
                hardware_service.update_led(color, True)
                time.sleep(0.5)
                
                print(f"  Turning OFF {color} LED")
                hardware_service.update_led(color, False)
                time.sleep(0.3)
        
        print("LED test completed successfully!")
        print("Check the WebUI at http://localhost:8000 to see the LED changes")
        
        # Keep running for a few seconds so user can see results
        print("Keeping system running for 10 seconds...")
        time.sleep(10)
        
    finally:
        print("Stopping BOSS system...")
        system_manager.stop()
        print("Test finished.")

if __name__ == "__main__":
    test_led_blinking()
