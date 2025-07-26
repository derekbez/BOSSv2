"""
Hello World Mini-App - Comprehensive BOSS API Demonstration
============================================================

This app serves as the definitive template for BOSS mini-app development,
demonstrating all key features and best practices:

- Screen text display with updates
- LED control and blinking sequences
- Button event handling with LED coordination
- Event subscription and cleanup
- Timeout handling and periodic actions
- Proper logging and error handling
- Clean shutdown procedures

Hardware Parity: This app works identically on real Pi hardware and WebUI development.
"""

import time
import threading


def run(stop_event, api):
    """
    Hello World app demonstrating comprehensive BOSS API usage.
    
    Features:
    - Displays welcome message on screen
    - Blinks LEDs in sequence twice at startup
    - Activates all four buttons (LEDs indicate availability)
    - Counts button presses and displays results
    - Auto-blinks LEDs again if no activity for 30 seconds
    - Clean shutdown with proper event unsubscription
    
    Args:
        stop_event: threading.Event to signal app termination
        api: BOSS API object with .screen, .hardware, .event_bus, .log_info, etc.
    """
    api.log_info("=== Hello World App Starting ===")
    
    # App state tracking
    button_counts = {"red": 0, "yellow": 0, "green": 0, "blue": 0}
    last_activity_time = time.time()
    subscription_ids = []  # Track subscriptions for cleanup
    
    # ========================================================================
    # SCREEN DISPLAY
    # ========================================================================
    
    def update_screen():
        """Update the screen with current button counts."""
        message = "Hello World!\n\n"
        
        if any(count > 0 for count in button_counts.values()):
            message += "Button Presses:\n"
            for color, count in button_counts.items():
                if count > 0:
                    message += f"  {color.title()}: {count}\n"
            message += "\nPress any button!"
        else:
            message += "Welcome to BOSS!\n\nPress any colored button\nto see the magic happen!"
        
        message += "\n\nMain button to exit"
        
        api.screen.display_text(message, font_size=28, align="center")
    
    # Display initial welcome message
    update_screen()
    
    # ========================================================================
    # LED CONTROL FUNCTIONS
    # ========================================================================
    
    def blink_led_sequence():
        """Blink each LED in sequence twice - demonstrates LED control."""
        api.log_info("Starting LED blink sequence")
        
        colors = ["red", "yellow", "green", "blue"]
        
        for cycle in range(2):  # Blink twice
            api.log_info(f"LED blink cycle {cycle + 1}/2")
            
            for color in colors:
                if stop_event.is_set():
                    return
                
                # Turn on current LED
                api.hardware.set_led(color, True)
                api.log_info(f"  Blinking {color} LED")
                
                # Wait briefly
                if stop_event.wait(0.3):
                    return
                
                # Turn off current LED  
                api.hardware.set_led(color, False)
                
                # Brief pause between LEDs
                if stop_event.wait(0.2):
                    return
            
            # Pause between cycles
            if cycle == 0:  # Pause only between cycles, not after last
                if stop_event.wait(0.5):
                    return
        
        api.log_info("LED blink sequence completed")
    
    def activate_all_buttons():
        """Turn on all LEDs to indicate all buttons are active."""
        api.log_info("Activating all buttons (turning on all LEDs)")
        for color in button_counts.keys():
            api.hardware.set_led(color, True)
    
    def deactivate_all_buttons():
        """Turn off all LEDs - buttons become inactive."""
        api.log_info("Deactivating all buttons (turning off all LEDs)")
        for color in button_counts.keys():
            api.hardware.set_led(color, False)
    
    # ========================================================================
    # BUTTON EVENT HANDLERS
    # ========================================================================
    
    def on_button_press(event_type, payload):
        """
        Handle button press events - follows LED/Button coordination pattern.
        
        Only processes button presses for buttons with LEDs currently on.
        Updates button count and refreshes screen display.
        """
        nonlocal last_activity_time
        
        button = payload.get("button") or payload.get("button_id")
        if not button or button not in button_counts:
            return
        
        # Update activity time
        last_activity_time = time.time()
        
        # Increment counter and update display
        button_counts[button] += 1
        count = button_counts[button]
        
        # Create dynamic message based on count
        if count == 1:
            press_message = f"{button.title()} button pressed!"
        else:
            press_message = f"{button.title()} button pressed {count} times!"
        
        api.log_info(press_message)
        
        # Briefly turn off the LED for visual feedback
        api.hardware.set_led(button, False)
        
        # Update screen immediately
        update_screen()
        
        # Turn LED back on after brief visual feedback
        def restore_led():
            if not stop_event.wait(0.2):
                api.hardware.set_led(button, True)
        
        threading.Thread(target=restore_led, daemon=True).start()
    
    def on_main_button_press(event_type, payload):
        """Handle main button press - exit the app."""
        button = payload.get("button") or payload.get("button_id")
        if button == "main":
            api.log_info("Main button pressed - initiating app shutdown")
            stop_event.set()
    
    # ========================================================================
    # TIMEOUT HANDLING
    # ========================================================================
    
    def check_activity_timeout():
        """Check if we need to blink LEDs due to inactivity."""
        nonlocal last_activity_time
        
        current_time = time.time()
        if current_time - last_activity_time >= 30.0:
            api.log_info("30 seconds of inactivity - running LED blink sequence")
            
            # Temporarily deactivate buttons during blink
            deactivate_all_buttons()
            
            # Run blink sequence
            blink_led_sequence()
            
            # Reactivate buttons if still running
            if not stop_event.is_set():
                activate_all_buttons()
            
            # Reset activity timer
            last_activity_time = current_time
    
    # ========================================================================
    # EVENT SUBSCRIPTION
    # ========================================================================
    
    try:
        # Subscribe to button events
        sub_id1 = api.event_bus.subscribe("button_pressed", on_button_press)
        sub_id2 = api.event_bus.subscribe("button_pressed", on_main_button_press)
        subscription_ids.extend([sub_id1, sub_id2])
        
        api.log_info("Event subscriptions created successfully")
        
        # ========================================================================
        # STARTUP SEQUENCE
        # ========================================================================
        
        # Initial LED blink sequence
        blink_led_sequence()
        
        # Activate all buttons if still running
        if not stop_event.is_set():
            activate_all_buttons()
            api.log_info("Hello World app fully initialized and ready")
        
        # ========================================================================
        # MAIN EVENT LOOP
        # ========================================================================
        
        while not stop_event.is_set():
            # Wait for 5 seconds or until stop signal
            if stop_event.wait(5.0):
                break
            
            # Check for activity timeout every 5 seconds
            check_activity_timeout()
        
    except Exception as e:
        api.log_error(f"Error in Hello World app main loop: {e}")
        import traceback
        api.log_error(f"Traceback: {traceback.format_exc()}")
    
    finally:
        # ========================================================================
        # CLEANUP AND SHUTDOWN
        # ========================================================================
        
        api.log_info("=== Hello World App Shutting Down ===")
        
        # Unsubscribe from all events
        for sub_id in subscription_ids:
            try:
                api.event_bus.unsubscribe(sub_id)
            except Exception as e:
                api.log_error(f"Error unsubscribing event {sub_id}: {e}")
        
        # Turn off all LEDs
        deactivate_all_buttons()
        
        # Clear screen
        api.screen.clear_screen()
        
        # Clear display if available
        if hasattr(api.hardware, 'set_display'):
            api.hardware.set_display(None)
        
        api.log_info("Hello World app cleanup completed")


if __name__ == "__main__":
    # This won't be called when run by BOSS, but useful for standalone testing
    print("Hello World Mini-App")
    print("=====================")
    print("This app should be run by the BOSS system.")
    print("Use: python -m boss.main")
    print("Then set switches to position 1 and press Go button.")
