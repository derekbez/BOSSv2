"""On This Day mini-app.

Shows notable events for today's date using byabbe.se API.

Enhancements (2025-08-31):
* Removed all truncation – full event descriptions are displayed.
* Added word-wrapping (configurable width) instead of slicing.
* Added paging (Yellow=Prev, Blue=Next, Green=Refresh) similar to list_all_apps.
* Manual refresh via green button still supported.
"""
from __future__ import annotations
import datetime as _dt
import time
import textwrap

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore


def fetch_events(month: int, day: int, timeout: float = 6.0):
    """Fetch full event descriptions (no truncation). Returns list of (year, description)."""
    if requests is None:
        raise RuntimeError("requests not available")
    url = f"https://byabbe.se/on-this-day/{month}/{day}/events.json"
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    events = data.get("events", [])
    out = []
    for e in events:  # include all; could be many but typically manageable
        year = e.get("year") or "?"
        desc = (e.get("description") or "").strip()
        if desc:
            out.append((year, desc))
    return out


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    refresh_seconds = float(cfg.get("refresh_seconds", 43200))  # half day default
    timeout = float(cfg.get("request_timeout_seconds", 6))
    wrap_width = int(cfg.get("wrap_width", 60))
    per_page = int(cfg.get("per_page", 18))  # lines per page (after wrapping)

    api.screen.clear_screen()
    title = "On This Day"
    api.hardware.set_led("green", True)  # refresh

    sub_ids = []
    last_fetch = 0.0
    events_cache: list[tuple[str, str]] = []
    wrapped_lines: list[str] = []
    page = 0

    def rebuild_wrapped_lines():
        nonlocal wrapped_lines
        wrapped_lines = []
        for year, desc in events_cache:
            first_prefix = f"{year}: "
            # Wrap keeping year only on first line
            raw_lines = textwrap.wrap(desc, width=wrap_width - len(first_prefix)) or [desc]
            for i, seg in enumerate(raw_lines):
                if i == 0:
                    wrapped_lines.append(first_prefix + seg)
                else:
                    wrapped_lines.append(" " * len(first_prefix) + seg)

    def total_pages() -> int:
        if not wrapped_lines:
            return 1
        return (len(wrapped_lines) - 1) // per_page + 1

    def set_nav_leds():
        api.hardware.set_led('yellow', page > 0)
        api.hardware.set_led('blue', page < total_pages() - 1)

    def display_page():
        lines = [title, ""]
        if not wrapped_lines:
            lines.append("(no events)")
        else:
            start = page * per_page
            end = start + per_page
            for l in wrapped_lines[start:end]:
                lines.append(l)
            lines.append("")
            lines.append(f"Page {page+1}/{total_pages()}  Lines={len(wrapped_lines)}")
            lines.append("[YEL] Prev  [GRN] Refresh  [BLU] Next")
        api.screen.display_text("\n".join(lines), font_size=18, align='left')
        set_nav_leds()

    def refresh_data():
        nonlocal events_cache, page, last_fetch
        try:
            today = _dt.date.today()
            events_cache = fetch_events(today.month, today.day, timeout=timeout)
            rebuild_wrapped_lines()
            page = 0
        except Exception as e:
            events_cache = []
            wrapped_lines.clear()
            api.screen.display_text(f"{title}\n\nErr: {e}", align='left')
        last_fetch = time.time()
        display_page()

    def on_button(ev):
        nonlocal page
        b = ev.get('button')
        if b == 'green':
            refresh_data()
        elif b == 'yellow' and page > 0:
            page -= 1
            display_page()
        elif b == 'blue' and page < total_pages() - 1:
            page += 1
            display_page()

    sub_ids.append(api.event_bus.subscribe('button_pressed', on_button))

    try:
        refresh_data()
        while not stop_event.is_set():
            if time.time() - last_fetch >= refresh_seconds:
                refresh_data()
            time.sleep(0.5)
    finally:
        for sid in sub_ids:
            api.event_bus.unsubscribe(sid)
        for c in ['red', 'yellow', 'green', 'blue']:
            api.hardware.set_led(c, False)
        api.screen.clear_screen()
