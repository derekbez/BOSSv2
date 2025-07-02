"""
Mini-app: Mini-App Directory Viewer (List All Apps)
Displays a paginated list of all available mini-apps by reading their number, name, and description from configuration files.
Entry point: run(stop_event, api)
"""
import os
from boss.core.paths import CONFIG_PATH, APPS_DIR
import json
from threading import Event
from typing import Any, List, Dict




def load_app_mappings() -> Dict[str, str]:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config.get('app_mappings', {})


def load_manifest(app_dir: str) -> Dict[str, Any]:
    manifest_path = os.path.join(APPS_DIR, app_dir, 'manifest.json')
    if not os.path.exists(manifest_path):
        return {}
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_app_list() -> List[Dict[str, Any]]:
    mappings = load_app_mappings()
    app_list = []
    for num in sorted(mappings, key=lambda x: int(x)):
        app_dir = mappings[num]
        manifest = load_manifest(app_dir)
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
    config = load_manifest('list_all_apps').get('config', {})
    per_page = config.get('entries_per_page', 15)
    app_list = get_app_list()
    total_pages = (len(app_list) - 1) // per_page + 1
    page = 0

    def display_page(page_idx: int):
        page_items = paginate(app_list, page_idx, per_page)
        lines = [
            "Num | Name                 | Description",
            "----+----------------------+--------------------------"
        ]
        for app in page_items:
            lines.append(f"{app['number']:>3} | {app['name'][:20]:<20} | {app['description'][:24]}")
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
            api.screen.print_line(line, size=28)

    display_page(page)

    # Event-driven: subscribe to button presses
    def on_button_press(event):
        nonlocal page
        button = event.get('button_id')
        if button == 'yellow' and page > 0:
            page -= 1
            display_page(page)
        elif button == 'blue' and page < total_pages - 1:
            page += 1
            display_page(page)

    sub_id = api.event_bus.subscribe(
        'input.button.pressed',
        on_button_press,
        filter={"button_id": ["yellow", "blue"]}
    )

    try:
        while not stop_event.is_set():
            stop_event.wait(0.2)
    finally:
        # Unsubscribe on exit
        api.event_bus.unsubscribe(sub_id)
