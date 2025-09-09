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
from typing import Optional
from boss.presentation.text.utils import wrap_events, estimate_char_columns, TextPaginator

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

    # Dynamic wrap width: if not explicitly set, approximate based on screen width.
    # Heuristic: assume ~10px per mono glyph at font_size 18; if logical screen_width
    # is present in config, derive char columns. Fallback to 100 for wider layout.
    default_wrap = 100
    try:
        boss_cfg = getattr(getattr(api, '_app_manager', None), 'config_manager', None)
        screen_w = None
        if boss_cfg is not None:
            root_cfg = getattr(boss_cfg, 'config', None)
            if isinstance(root_cfg, dict):
                screen_w = ((root_cfg.get('hardware') or {}).get('screen_width'))
            else:
                eff = getattr(boss_cfg, 'get_effective_config', None)
                if callable(eff):
                    _cfg_obj = eff()
                    screen_w = getattr(getattr(_cfg_obj, 'hardware', None), 'screen_width', None)
        if isinstance(screen_w, (int, float)) and screen_w > 200:
            default_wrap = estimate_char_columns(int(screen_w), font_size=18)
    except Exception:
        pass
    wrap_width = int(cfg.get("wrap_width", default_wrap))

    per_page = int(cfg.get("per_page", 18))  # lines per page (after wrapping)

    api.screen.clear_screen()
    title = "On This Day"
    # Green LED indicates manual refresh availability ONLY when we are outside the post-fetch cooldown.
    # At start we allow refresh (data not yet loaded) so keep it on until first fetch completes.
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0
    events_cache: list[tuple[str, str]] = []
    wrapped_lines: list[str] = []
    paginator: TextPaginator | None = None

    def rebuild_wrapped_lines():
        nonlocal wrapped_lines, paginator
        wrapped_lines = wrap_events(events_cache, wrap_width)
        if paginator is None:
            paginator = TextPaginator(
                wrapped_lines,
                per_page,
                led_update=lambda color, state: api.hardware.set_led(color, state),
                prev_color='yellow',
                next_color='blue'
            )
        else:
            paginator.set_lines(wrapped_lines)
            paginator.reset()

    def total_pages() -> int:
        if paginator is None:
            return 1
        return paginator.total_pages

    def set_nav_leds():
        if paginator:
            paginator._update_leds()  # internal LED update for prev/next
        # Green only on if refresh window elapsed (manual refresh meaningful)
        can_refresh = (time.time() - last_fetch) >= refresh_seconds
        api.hardware.set_led('green', can_refresh)

    def display_page():
        lines = [title, ""]
        if not wrapped_lines:
            lines.append("(no events)")
        else:
            current_lines = paginator.page_lines() if paginator else []
            for l in current_lines:
                lines.append(l)
            lines.append("")
            page_num = (paginator.page + 1) if paginator else 1
            lines.append(f"Page {page_num}/{total_pages()}  Lines={len(wrapped_lines)}")
            lines.append("[YEL] Prev  [GRN] Refresh  [BLU] Next")
        # Disable backend wrap to avoid double wrapping; we already wrapped.
        api.screen.display_text("\n".join(lines), font_size=18, align='left', wrap=False)
        set_nav_leds()

    def refresh_data():
        nonlocal events_cache, last_fetch
        try:
            today = _dt.date.today()
            events_cache = fetch_events(today.month, today.day, timeout=timeout)
            rebuild_wrapped_lines()
        except Exception as e:
            events_cache = []
            wrapped_lines.clear()
            api.screen.display_text(f"{title}\n\nErr: {e}", align='left')
        last_fetch = time.time()
        display_page()

    # Updated handler signature (event_type, event) as per standardized pattern
    def on_button(event_type, ev):
        b = ev.get('button')
        if b == 'green':
            refresh_data()
        elif b == 'yellow' and paginator and paginator.prev():
            display_page()
        elif b == 'blue' and paginator and paginator.next():
            display_page()

    sub_ids.append(api.event_bus.subscribe('button_pressed', on_button))

    try:
        refresh_data()
        while not stop_event.is_set():
            # Periodic refresh after interval
            if time.time() - last_fetch >= refresh_seconds:
                refresh_data()
            else:
                # Update green LED availability if threshold just crossed
                set_nav_leds()
            time.sleep(0.5)
    finally:
        for sid in sub_ids:
            api.event_bus.unsubscribe(sid)
        for c in ['red', 'yellow', 'green', 'blue']:
            api.hardware.set_led(c, False)
        api.screen.clear_screen()
