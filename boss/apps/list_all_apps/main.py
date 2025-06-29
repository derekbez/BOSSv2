"""
Mini-app: Mini-App Directory Viewer (List All Apps)
Displays a paginated list of all available mini-apps by reading their number, name, and description from configuration files.
Entry point: run(stop_event, api)
"""
import os
import json
from threading import Event
from typing import Any, List, Dict

APPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'BOSSsettings.json'))


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
    Main entry point for the Mini-App Directory Viewer mini-app.
    Args:
        stop_event (Event): Event to signal app termination.
        api (object): Provided API for hardware/display access.
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
        if page_idx == 0:
            lines.append("[YELLOW: DISABLED] Prev | [BLUE] Next")
        elif page_idx == total_pages - 1:
            lines.append("[YELLOW] Prev | [BLUE: DISABLED] Next")
        else:
            lines.append("[YELLOW] Prev | [BLUE] Next")
        api.screen.clear()
        api.screen.set_cursor(0)
        for line in lines:
            api.screen.print_line(line, size=28)

    display_page(page)

    while not stop_event.is_set():
        event = api.wait_for_button(['yellow', 'blue'], timeout=0.2)
        if event == 'yellow' and page > 0:
            page -= 1
            display_page(page)
        elif event == 'blue' and page < total_pages - 1:
            page += 1
            display_page(page)
        # else: ignore or debounce
