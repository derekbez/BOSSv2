"""
Hello World Mini-App - Demonstrates the new event-driven BOSS API.
"""

import time

def run(stop_event, api):
    """
    Simple hello world app that responds to button presses.
    
    Args:
        stop_event: threading.Event to signal app termination
        api: BOSS API object with .screen, .hardware, .event_bus
    """
    api.log_info("Hello World app starting")
    
    # Display welcome message
    api.screen.display_text("Hello World!\n\nPress colored buttons to see events\nGo button to exit", 
                           font_size=32, align="center")
    
    # Set initial LED states - all off
    for color in ["red", "yellow", "green", "blue"]:
        api.hardware.set_led(color, False)
    
    # Track button states
    button_count = {"red": 0, "yellow": 0, "green": 0, "blue": 0}
    
    def on_button_press(event_type, payload):
        """Handle button press events."""
        button = payload.get("button")
        if button in button_count:
            button_count[button] += 1
            count = button_count[button]
            
            # Light up the LED for the pressed button
            api.hardware.set_led(button, True, brightness=0.8)
            
            # Update screen with button press count
            message = f"Hello World!\n\nButton Presses:\n"
            for color, count_val in button_count.items():
                message += f"{color.title()}: {count_val}\n"
            message += "\nGo button to exit"
            
            api.screen.display_text(message, font_size=24, align="center")
            api.log_info(f"{button.title()} button pressed ({count} times)")
    
    def on_button_release(event_type, payload):
        """Handle button release events."""
        button = payload.get("button")
        if button in button_count:
            # Turn off the LED when button is released
            api.hardware.set_led(button, False)
            api.log_info(f"{button.title()} button released")
    
    # Subscribe to button events
    api.event_bus.subscribe("button_pressed", on_button_press)
    api.event_bus.subscribe("button_released", on_button_release)
    
    # Show current switch value on 7-segment display
    def on_switch_change(event_type, payload):
        """Handle switch change events."""
        new_value = payload.get("new_value", 0)
        api.hardware.set_display(new_value)
        api.log_info(f"Switch value changed to: {new_value}")
    
    api.event_bus.subscribe("switch_changed", on_switch_change)
    
    # Main app loop - just wait for stop signal
    try:
        api.log_info("Hello World app running - waiting for events")
        
        # Blink display every 2 seconds to show app is alive
        blink_count = 0
        while not stop_event.is_set():
            if stop_event.wait(2.0):  # Wait 2 seconds or until stop
                break
            
            # Blink display
            blink_count += 1
            if blink_count % 2 == 0:
                api.hardware.set_display(None)  # Clear display
            else:
                api.hardware.set_display(0)  # Show 0
            
    except Exception as e:
        api.log_error(f"Error in Hello World app: {e}")
    
    finally:
        # Clean up - turn off all LEDs
        for color in ["red", "yellow", "green", "blue"]:
            api.hardware.set_led(color, False)
        
        api.screen.clear_screen()
        api.hardware.set_display(None)
        api.log_info("Hello World app stopping")

if __name__ == "__main__":
    # This won't be called when run by BOSS, but useful for testing
    print("Hello World mini-app - should be run by BOSS system")
