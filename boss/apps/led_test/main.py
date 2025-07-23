"""
LED Test Mini-App - Tests LED functionality.
"""

import time

def run(stop_event, api):
    """
    Test app for LED functionality.
    
    Args:
        stop_event: threading.Event to signal app termination
        api: BOSS API object with .screen, .hardware, .event_bus
    """
    api.log_info("LED Test app starting")
    
    # Display instructions
    api.screen.display_text("LED Test\n\nAutomatically cycling\nthrough all LEDs\n\nGo button to exit", 
                           font_size=24, align="center")
    
    colors = ["red", "yellow", "green", "blue"]
    current_color = 0
    
    def on_go_button(event_type, payload):
        """Handle go button press."""
        api.log_info("Go button pressed - exiting LED Test")
        stop_event.set()
    
    # Subscribe to go button
    api.event_bus.subscribe("go_button_press", on_go_button)
    
    api.log_info("LED Test app running - cycling LEDs")
    
    # Main LED cycling loop
    try:
        while not stop_event.is_set():
            # Turn off all LEDs
            for color in colors:
                api.hardware.set_led(color, False)
            
            # Turn on current LED
            color = colors[current_color]
            api.hardware.set_led(color, True, brightness=0.8)
            
            # Update screen
            api.screen.display_text(f"LED Test\n\nCurrently showing:\n{color.upper()} LED\n\nGo button to exit", 
                                   font_size=24, align="center", color=color)
            
            api.log_info(f"LED Test: {color} LED on")
            
            # Wait or check for stop
            for _ in range(20):  # 2 seconds in 0.1s increments
                if stop_event.is_set():
                    break
                stop_event.wait(0.1)
            
            # Move to next color
            current_color = (current_color + 1) % len(colors)
            
    except KeyboardInterrupt:
        pass
    finally:
        # Turn off all LEDs
        for color in colors:
            api.hardware.set_led(color, False)
        
        api.screen.display_text("LED Test Stopped", font_size=24, align="center")
        api.log_info("LED Test app stopping")
