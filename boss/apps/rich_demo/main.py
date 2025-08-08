"""
Rich Display Demo App - Showcases Rich-specific features

This app demonstrates the enhanced display capabilities available when using 
the Rich backend, including tables, progress bars, panels, trees, syntax 
highlighting, and markup formatting.
"""
import time
import random
from typing import Dict, Any


def run(stop_event, api) -> None:
    """
    Main entry point for the Rich Display Demo app.
    
    Demonstrates various Rich-specific display features including:
    - Tables with formatted data
    - Progress bars with animation
    - Panels with borders and titles
    - Tree structures for hierarchical data
    - Syntax-highlighted code
    - Rich markup formatting
    
    Args:
        stop_event: Threading event to signal when to stop
        api: BOSS API object for hardware/display access
    """
    try:
        # Check if we're using Rich backend
        screen = api.hardware.screen
        is_rich_backend = hasattr(screen, 'display_table')
        
        if not is_rich_backend:
            # Fallback for Pillow backend
            api.hardware.screen.display_text(
                "Rich Demo App\n\nRequires Rich backend\nSwitch to Rich in config",
                color="yellow", background="red", align="center"
            )
            time.sleep(5)
            return
        
        # Demo 1: Welcome with Rich markup
        api.hardware.screen.display_markup(
            "[bold blue]Rich Display Demo[/bold blue]\n\n"
            "[green]Showcasing enhanced display features[/green]\n"
            "[yellow]Press any button to continue...[/yellow]"
        )
        
        # Set all LEDs on to indicate any button can be pressed
        for color in ['red', 'yellow', 'green', 'blue']:
            api.hardware.set_led(color, True)
        
        # Wait for button press or stop event
        button_pressed = wait_for_button_or_stop(api, stop_event, timeout=10)
        if stop_event.is_set():
            return
        
        # Demo 2: Data table
        if not stop_event.is_set():
            demo_table(api, stop_event)
        
        # Demo 3: Progress bar animation
        if not stop_event.is_set():
            demo_progress(api, stop_event)
        
        # Demo 4: Panel with information
        if not stop_event.is_set():
            demo_panel(api, stop_event)
        
        # Demo 5: Tree structure
        if not stop_event.is_set():
            demo_tree(api, stop_event)
        
        # Demo 6: Syntax highlighting
        if not stop_event.is_set():
            demo_code(api, stop_event)
        
        # Final message
        api.hardware.screen.display_markup(
            "[bold green]Rich Demo Complete![/bold green]\n\n"
            "[cyan]Rich backend provides enhanced\ndisplay capabilities for apps[/cyan]"
        )
        time.sleep(3)
        
    finally:
        # Clean up LEDs
        for color in ['red', 'yellow', 'green', 'blue']:
            api.hardware.set_led(color, False)


def wait_for_button_or_stop(api, stop_event, timeout=5):
    """Wait for any button press or stop event with timeout."""
    button_pressed = False
    
    def button_handler(event):
        nonlocal button_pressed
        button_pressed = True
    
    # Subscribe to button events
    sub_id = api.event_bus.subscribe('button_pressed', button_handler)
    
    try:
        start_time = time.time()
        while not button_pressed and not stop_event.is_set():
            if time.time() - start_time > timeout:
                break
            time.sleep(0.1)
        return button_pressed
    finally:
        api.event_bus.unsubscribe(sub_id)


def demo_table(api, stop_event):
    """Demonstrate Rich table display."""
    # Sample system information table
    system_data = {
        "CPU": {"Usage": "45%", "Temp": "62°C", "Cores": "4"},
        "Memory": {"Used": "2.1GB", "Free": "1.9GB", "Total": "4.0GB"}, 
        "Storage": {"Used": "15GB", "Free": "45GB", "Total": "60GB"},
        "Network": {"Status": "Connected", "IP": "192.168.1.100", "Speed": "100Mbps"}
    }
    
    api.hardware.screen.display_table(system_data, "System Status")
    time.sleep(3)
    
    if stop_event.is_set():
        return
    
    # Sample app statistics table
    app_stats = {
        "rich_demo": 15,
        "hello_world": 23, 
        "matrix_rain": 8,
        "joke_display": 42,
        "system_info": 3
    }
    
    api.hardware.screen.display_table(app_stats, "App Usage Statistics")
    time.sleep(3)


def demo_progress(api, stop_event):
    """Demonstrate animated progress bar."""
    # Simulate a loading process
    for progress in range(0, 101, 5):
        if stop_event.is_set():
            break
        
        api.hardware.screen.display_progress(progress, "Loading Rich Demo...")
        time.sleep(0.2)
    
    time.sleep(1)


def demo_panel(api, stop_event):
    """Demonstrate Rich panel display."""
    panel_content = (
        "Rich Backend Features:\n\n"
        "• Tables for structured data\n"
        "• Progress bars with animation\n" 
        "• Panels with borders\n"
        "• Tree structures\n"
        "• Syntax highlighting\n"
        "• Rich markup formatting"
    )
    
    api.hardware.screen.display_panel(panel_content, "Feature Overview", "green")
    time.sleep(4)


def demo_tree(api, stop_event):
    """Demonstrate Rich tree structure display."""
    system_tree = {
        "BOSS System": {
            "Hardware": {
                "Switches": "8 toggle switches",
                "Buttons": "4 color + 1 main",
                "Display": "7-segment TM1637",
                "Screen": "7-inch HDMI"
            },
            "Software": {
                "Backend": "Rich display",
                "Apps": ["rich_demo", "hello_world", "matrix_rain"],
                "Config": "JSON-based"
            },
            "Features": {
                "Remote": "SSH management",
                "Logs": "Centralized logging", 
                "Testing": "Comprehensive tests"
            }
        }
    }
    
    api.hardware.screen.display_tree(system_tree, "BOSS Architecture")
    time.sleep(4)


def demo_code(api, stop_event):
    """Demonstrate syntax highlighting."""
    sample_code = '''def hello_boss():
    """Simple BOSS app example."""
    print("Hello from BOSS!")
    return {"status": "success"}

# Run the app
if __name__ == "__main__":
    result = hello_boss()
    print(f"Result: {result}")'''
    
    api.hardware.screen.display_code(sample_code, "python", "monokai")
    time.sleep(4)