"""
Mini-app: Mini-App Directory Viewer (List All Apps)
Displays a paginated list of all available mini-apps by reading their number, name, and description from configuration files.
Entry point: run(stop_event, api)
"""

from threading import Event
from typing import Any, List, Dict


def get_app_list(api: Any) -> List[Dict[str, Any]]:
    """Get list of all apps from the API."""
    # Get all apps through the API instead of directly accessing config
    try:
        # Prefer cached summaries from API if available
        if hasattr(api, 'get_app_summaries'):
            summaries = api.get_app_summaries()
            if isinstance(summaries, list) and summaries:
                return summaries

        # Fallback to building from full app objects
        all_apps_dict = api.get_all_apps()
        app_list = []
        for switch_value, app in all_apps_dict.items():
            app_list.append({
                'number': str(switch_value).zfill(3),
                'name': app.manifest.name,
                'description': getattr(app.manifest, 'description', '') or ''
            })
        app_list.sort(key=lambda x: int(x['number']))
        return app_list
    except Exception as e:
        api.log_error(f"Error getting app list: {e}")
        return []


def paginate(items: List[Dict[str, Any]], page: int, per_page: int) -> List[Dict[str, Any]]:
    start = page * per_page
    end = start + per_page
    return items[start:end]


def run(stop_event: Event, api: Any) -> None:
    """
    Main entry point for the Mini-App Directory Viewer mini-app (event-driven).
    Args:
        stop_event (Event): Event to signal app termination.
        api (AppAPI): Provided API for hardware/display access.
    """
    # Use default configuration values since we don't have ConfigManager access
    per_page = 24  # Default entries per page
    app_list = get_app_list(api)
    
    if not app_list:
        # If no apps found, show error message
        api.screen.clear_screen()
        api.screen.display_text("Error: No apps found\nCheck configuration", font_size=16, align='center')
        return
    
    total_pages = (len(app_list) - 1) // per_page + 1
    page = 0

    def display_page(page_idx: int):
        page_items = paginate(app_list, page_idx, per_page)
        
        # Build the display text
        lines = [
            "Mini-Apps Directory",
            "===================",
            "",
            "Num | Name",
            "----+---------------------------------------------"
        ]
        
        for app in page_items:
            lines.append(f"{app['number']:>3} | {app['name'][:45]:<45}")
        
        lines.append("")
        lines.append(f"Page {page_idx+1}/{total_pages}")
        
        # LED logic: illuminate available buttons
        if page_idx == 0 and total_pages == 1:
            lines.append("[YELLOW: DISABLED] Prev | [BLUE : DISABLED] Next")
            api.hardware.set_led('yellow', False)
            api.hardware.set_led('blue', False)
        elif page_idx == 0:
            lines.append("[YELLOW: DISABLED] Prev | [BLUE] Next")
            api.hardware.set_led('yellow', False)
            api.hardware.set_led('blue', True)
        elif  page_idx == total_pages - 1:
            lines.append("[YELLOW] Prev | [BLUE: DISABLED] Next")
            api.hardware.set_led('yellow', True)
            api.hardware.set_led('blue', False)
        else:
            lines.append("[YELLOW] Prev | [BLUE] Next")
            api.hardware.set_led('yellow', True)
            api.hardware.set_led('blue', True)
        
        # Display the text
        display_text = "\n".join(lines)
        api.screen.clear_screen()
        api.screen.display_text(display_text, font_size=12, align="left")    

    display_page(page)

    # Event-driven: subscribe to button presses
    def on_button_press(event_type, payload):
        nonlocal page
        api.log_info(f"Button event received: {event_type} | {payload}")
        
        # Handle button press events
        button = payload.get('button_id') or payload.get('button')
        if button == 'yellow' and page > 0:
            page -= 1
            display_page(page)
        elif button == 'blue' and page < total_pages - 1:
            page += 1
            display_page(page)

    sub_id = api.event_bus.subscribe(
        'button_pressed',
        on_button_press
    )

    try:
        while not stop_event.is_set():
            stop_event.wait(0.2)
    finally:
        # Unsubscribe on exit
        api.event_bus.unsubscribe(sub_id)
