"""
Button Test Mini-App - Tests colored button functionality.
"""

def run(stop_event, api):
    """
    Test app for button functionality.
    
    Args:
        stop_event: threading.Event to signal app termination
        api: BOSS API object with .screen, .hardware, .event_bus
    """
    api.log_info("Button Test app starting")
    
    # Display instructions
    api.screen.display_text("Button Test\n\nPress colored buttons\nto test functionality\n\nGo button to exit", 
                           font_size=24, align="center")
    
    # Track button states
    button_states = {"red": False, "yellow": False, "green": False, "blue": False}
    
    def on_button_press(event_type, payload):
        """Handle button press events."""
        button = payload.get("button")
        if button in button_states:
            button_states[button] = True
            api.hardware.set_led(button, True, brightness=1.0)
            
            api.screen.display_text(f"Button Test\n\n{button.upper()} BUTTON\nPRESSED!\n\nGo button to exit", 
                                   font_size=24, align="center", color=button)
            api.log_info(f"{button.title()} button pressed")
    
    def on_button_release(event_type, payload):
        """Handle button release events."""
        button = payload.get("button")
        if button in button_states:
            button_states[button] = False
            api.hardware.set_led(button, False)
            
            api.screen.display_text("Button Test\n\nPress colored buttons\nto test functionality\n\nGo button to exit", 
                                   font_size=24, align="center")
            api.log_info(f"{button.title()} button released")
    
    def on_go_button(event_type, payload):
        """Handle go button press."""
        api.log_info("Go button pressed - exiting Button Test")
        stop_event.set()
    
    # Subscribe to events
    api.event_bus.subscribe("button_press", on_button_press)
    api.event_bus.subscribe("button_release", on_button_release)
    api.event_bus.subscribe("go_button_press", on_go_button)
    
    api.log_info("Button Test app running - waiting for events")
    
    # Main event loop
    try:
        while not stop_event.is_set():
            stop_event.wait(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        # Turn off all LEDs
        for color in button_states.keys():
            api.hardware.set_led(color, False)
        
        api.screen.display_text("Button Test Stopped", font_size=24, align="center")
        api.log_info("Button Test app stopping")
