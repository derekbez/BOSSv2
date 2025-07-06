"""
Mini-app: Mini-App Directory Viewer (List All Apps)
Displays a paginated list of all available mini-apps by reading their number, name, and description from configuration files.
Entry point: run(stop_event, api)
"""

from boss.core.config import ConfigManager
from threading import Event
from typing import Any, List, Dict


def get_app_list() -> List[Dict[str, Any]]:
    config_mgr = ConfigManager()
    mappings = config_mgr.app_mappings
    app_list = []
    for num in sorted(mappings, key=lambda x: int(x)):
        mapping = mappings[num]
        # Support both legacy (str) and new (dict) mapping formats
        if isinstance(mapping, dict):
            app_dir = mapping.get('app', num)
        else:
            app_dir = mapping
        manifest = config_mgr.get_manifest(app_dir)
        if manifest:
            app_list.append({
                'number': num.zfill(3),
                'name': manifest.get('title', app_dir),
                'description': manifest.get('description', '')
            })
    return app_list


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
    config_mgr = ConfigManager()
    config = config_mgr.get_manifest('list_all_apps').get('config', {})
    per_page = config.get('entries_per_page', 15)
    app_list = get_app_list()
    total_pages = (len(app_list) - 1) // per_page + 1
    page = 0

    def display_page(page_idx: int):
        page_items = paginate(app_list, page_idx, per_page)
        num_col = 3   # Number of characters in the "Num" column (excluding spaces)
        name_col = 45 # Number of characters in the "Name" column (excluding spaces)
        lines = [
            "Num | Name",
            f"{'-' * num_col}+{'-' * name_col}"
        ]
        for app in page_items:
            lines.append(f"{app['number']:>3} | {app['name'][:45]:<45}")
        lines.append("")
        lines.append(f"Page {page_idx+1}/{total_pages}")
        # LED logic: illuminate available buttons
        led_states = {'yellow': False, 'blue': False}
        if page_idx == 0:
            lines.append("[YELLOW: DISABLED] Prev | [BLUE] Next")
            led_states['yellow'] = False
            led_states['blue'] = True
        elif page_idx == total_pages - 1:
            lines.append("[YELLOW] Prev | [BLUE: DISABLED] Next")
            led_states['yellow'] = True
            led_states['blue'] = False
        else:
            lines.append("[YELLOW] Prev | [BLUE] Next")
            led_states['yellow'] = True
            led_states['blue'] = True
        api.set_leds(led_states)
        api.screen.clear()
        api.screen.set_cursor(0)
        for line in lines:
            api.screen.print_line(line, size=api.FONT_SIZE_SMALLER, align='left')
        #api.screen.refresh()    

    display_page(page)

    # Event-driven: subscribe to button presses
    def on_button_press(event_type, event):
        nonlocal page
        api.logger.info(f"[list_all_apps] Button event received: {event_type} | {event}")
        # Only respond to button press, not release
        if event_type != 'input.button.pressed':
            return
        button = event.get('button_id') or event.get('button')
        if button == 'yellow' and page > 0:
            page -= 1
            display_page(page)
        elif button == 'blue' and page < total_pages - 1:
            page += 1
            display_page(page)

    sub_id = api.event_bus.subscribe(
        'input.button.pressed',
        on_button_press,
        filter=None  # Let handler filter for robustness
    )

    try:
        while not stop_event.is_set():
            stop_event.wait(0.2)
    finally:
        # Unsubscribe on exit
        api.event_bus.unsubscribe(sub_id)
