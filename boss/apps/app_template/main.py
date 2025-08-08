"""
Enhanced BOSS App Template with Rich Backend Support

This template demonstrates best practices for creating BOSS apps that work
with both Pillow and Rich backends, with enhanced features when Rich is available.
"""
import time
import random
from typing import Dict, Any


def run(stop_event, api) -> None:
    """
    Enhanced app template with Rich backend support.
    
    Demonstrates:
    - Feature detection for backend compatibility
    - Graceful degradation between Rich and Pillow
    - Proper LED/button coordination
    - Rich-specific features when available
    - Error handling and cleanup
    
    Args:
        stop_event: Threading event to signal when to stop
        api: BOSS API object for hardware/display access
    """
    try:
        # Detect which backend is available
        screen = api.hardware.screen
        is_rich_backend = hasattr(screen, 'display_table')
        backend_name = "Rich" if is_rich_backend else "Pillow"
        
        # Show welcome message with backend info
        if is_rich_backend:
            screen.display_markup(
                f"[bold green]Enhanced App Template[/bold green]\\n\\n"
                f"Backend: [cyan]{backend_name}[/cyan]\\n"
                f"Features: [yellow]Rich Enhanced[/yellow]\\n\\n"
                f"[dim]Press any button to continue...[/dim]"
            )
        else:
            screen.display_text(
                f"Enhanced App Template\\n\\nBackend: {backend_name}\\nFeatures: Basic\\n\\nPress any button to continue...",
                color="white", background="blue", align="center"
            )
        
        # Setup LED/button coordination - all buttons active
        for color in ['red', 'yellow', 'green', 'blue']:
            api.hardware.set_led(color, True)
        
        # Wait for button press
        button_pressed = wait_for_button_or_stop(api, stop_event, timeout=10)
        if stop_event.is_set():
            return
        
        # Demonstrate features based on backend
        if is_rich_backend:
            demonstrate_rich_features(api, stop_event)
        else:
            demonstrate_basic_features(api, stop_event)
        
    except Exception as e:
        # Error handling with backend-appropriate display
        error_msg = f"App Error: {str(e)}"
        if hasattr(api.hardware.screen, 'display_panel'):
            api.hardware.screen.display_panel(error_msg, "Error", "red")
        else:
            api.hardware.screen.display_text(error_msg, color="white", background="red")
        time.sleep(3)
        
    finally:
        # Always clean up LEDs
        cleanup_leds(api)


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


def demonstrate_rich_features(api, stop_event):
    """Demonstrate Rich-specific enhanced features."""
    screen = api.hardware.screen
    
    # Demo 1: System information table
    if not stop_event.is_set():
        system_data = {
            "System": {"OS": "Raspberry Pi OS", "Python": "3.11+", "Arch": "ARM64"},
            "BOSS": {"Version": "2.0", "Backend": "Rich", "Status": "Running"},
            "Hardware": {"LEDs": "4", "Buttons": "4+1", "Display": "7-segment"}
        }
        screen.display_table(system_data, "System Information")
        time.sleep(3)
    
    # Demo 2: Progress simulation
    if not stop_event.is_set():
        for progress in range(0, 101, 10):
            if stop_event.is_set():
                break
            screen.display_progress(progress, f"Processing... {progress}%")
            time.sleep(0.3)
    
    # Demo 3: Feature showcase panel
    if not stop_event.is_set():
        panel_content = (
            "Rich Backend Features:\\n\\n"
            "✅ Tables for structured data\\n"
            "✅ Progress bars with animation\\n"
            "✅ Panels with borders and titles\\n"
            "✅ Tree structures for hierarchies\\n"
            "✅ Syntax highlighting for code\\n"
            "✅ Rich markup formatting"
        )
        screen.display_panel(panel_content, "Available Features", "green")
        time.sleep(4)
    
    # Demo 4: Application tree structure
    if not stop_event.is_set():
        app_structure = {
            "Enhanced App": {
                "Features": {
                    "Backend Detection": "Automatic",
                    "Rich Support": "Full",
                    "Fallback": "Graceful"
                },
                "Components": {
                    "Display": "Rich/Pillow",
                    "LEDs": "4 colors",
                    "Buttons": "4 + main"
                }
            }
        }
        screen.display_tree(app_structure, "App Architecture")
        time.sleep(4)
    
    # Demo 5: Code example
    if not stop_event.is_set():
        sample_code = '''def boss_app(stop_event, api):
    """Example BOSS app with Rich support."""
    screen = api.hardware.screen
    
    if hasattr(screen, 'display_table'):
        # Rich backend available
        data = {"Status": "Rich enabled"}
        screen.display_table(data, "Info")
    else:
        # Fallback to basic display
        screen.display_text("Basic mode")'''
        
        screen.display_code(sample_code, "python", "monokai")
        time.sleep(4)


def demonstrate_basic_features(api, stop_event):
    """Demonstrate basic features that work with any backend."""
    screen = api.hardware.screen
    
    # Demo 1: Multi-line text with colors
    if not stop_event.is_set():
        screen.display_text(
            "Enhanced App Template\\n\\nRunning in Basic Mode\\nAll core features available",
            color="white", background="green", align="center"
        )
        time.sleep(3)
    
    # Demo 2: Simulated progress with text
    if not stop_event.is_set():
        for i in range(0, 11):
            if stop_event.is_set():
                break
            progress = i * 10
            screen.display_text(
                f"Processing...\\n\\nProgress: {progress}%\\n{'█' * (i//2)}{'░' * (5-i//2)}",
                color="yellow", background="blue", align="center"
            )
            time.sleep(0.5)
    
    # Demo 3: Feature list
    if not stop_event.is_set():
        features = [
            "✓ Text display with colors",
            "✓ Multi-line text support", 
            "✓ Screen clearing",
            "✓ Alignment options",
            "✓ Cross-backend compatibility"
        ]
        screen.display_text("\\n".join(features), color="green", align="left")
        time.sleep(4)
    
    # Demo 4: Status information
    if not stop_event.is_set():
        screen.display_text(
            "Status: Basic Mode\\nBackend: Pillow\\nFeatures: Core Only\\n\\nUpgrade to Rich for\\nenhanced features!",
            color="white", background="purple", align="center"
        )
        time.sleep(3)


def cleanup_leds(api):
    """Clean up all LEDs."""
    for color in ['red', 'yellow', 'green', 'blue']:
        api.hardware.set_led(color, False)