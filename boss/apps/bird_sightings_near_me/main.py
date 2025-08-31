"""Bird Sightings Near Me mini-app.

Displays recent nearby bird species using the eBird API (no auth for recent observations endpoint
with lat/long). Allows manual refresh with green button.
"""
from __future__ import annotations
from typing import Any, List
import os
import logging
from boss.infrastructure.config.secrets_manager import secrets
import time
from textwrap import shorten

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

API_URL_TMPL = "https://api.ebird.org/v2/data/obs/geo/recent?lat={lat}&lng={lng}&dist={radius}&back=7"
EBIRD_DOCS_URL = "https://documenter.getpostman.com/view/664302/S1ENwy59"
USER_AGENT = "BOSS-MiniApp/1.0"


def fetch_sightings(lat: float, lng: float, radius: int, api_key: str | None, timeout: float = 6.0) -> list[tuple[str, str]]:
    if requests is None:
        raise RuntimeError("requests not available")
    url = API_URL_TMPL.format(lat=lat, lng=lng, radius=radius)
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if api_key:
        headers["X-eBirdApiToken"] = api_key.strip()
    r = requests.get(url, timeout=timeout, headers=headers)
    if r.status_code == 403 and not api_key:
        # Provide a more explicit hint for missing API key
        raise RuntimeError("403 Forbidden (missing eBird API key). Set BOSS_APP_EBIRD_API_KEY or app config 'api_key'.")
    r.raise_for_status()
    data: List[dict[str, Any]] = r.json()
    sightings: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for entry in data:  # collect all, de-duplicate
        name = entry.get("comName") or entry.get("species") or entry.get("sciName")
        loc = entry.get("locName") or ""
        if name:
            key = (name, loc)
            if key not in seen:
                sightings.append(key)
                seen.add(key)
    if not sightings:
        raise ValueError("No sightings")
    return sightings


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    # Prefer global system location if defined; fallback to app config / defaults
    global_loc = api.get_global_location() if hasattr(api, "get_global_location") else {}
    if global_loc and global_loc.get("latitude") is not None and global_loc.get("longitude") is not None:
        try:
            lat = float(global_loc.get("latitude"))  # type: ignore[arg-type]
            lng = float(global_loc.get("longitude"))  # type: ignore[arg-type]
        except Exception:
            lat = float(cfg.get("latitude", 51.5074))
            lng = float(cfg.get("longitude", -0.1278))
    else:
        lat = float(cfg.get("latitude", 51.5074))
        lng = float(cfg.get("longitude", -0.1278))
    radius = int(cfg.get("radius", 10))  # configurable via manifest config
    per_page = int(cfg.get("per_page", 10))  # number of sighting rows per page
    request_timeout = float(cfg.get("request_timeout_seconds", 6))
    api_key = (
        cfg.get("api_key")
        or secrets.get("BOSS_APP_EBIRD_API_KEY")
        or secrets.get("EBIRD_API_KEY")
        or os.environ.get("BOSS_APP_EBIRD_API_KEY")
        or os.environ.get("EBIRD_API_KEY")
        or api.get_config_value("EBIRD_API_KEY")
    )
    if not api_key:
        logging.getLogger(__name__).info(
            "bird_sightings_near_me: no API key resolved (looked for config 'api_key', env BOSS_APP_EBIRD_API_KEY / EBIRD_API_KEY, or manifest EBIRD_API_KEY)."
        )
    refresh_seconds = float(cfg.get("refresh_seconds", 120))

    api.screen.clear_screen()
    title = "Nearby Birds"
    api.hardware.set_led("green", True)  # refresh

    sub_ids: list[str] = []
    last_fetch = 0.0
    sightings_cache: list[tuple[str, str]] = []
    page = 0

    def compute_pages() -> int:
        if not sightings_cache:
            return 1
        return (len(sightings_cache) - 1) // per_page + 1

    def set_nav_leds():
        total_pages = compute_pages()
        # Yellow = prev, Blue = next
        api.hardware.set_led("yellow", page > 0)
        api.hardware.set_led("blue", page < total_pages - 1)

    def display_page():
        lines = [title, ""]
        if not sightings_cache:
            lines.append("(no data)")
        else:
            total_pages = compute_pages()
            start = page * per_page
            end = start + per_page
            for name, loc in sightings_cache[start:end]:
                display = f"{name} @ {loc}" if loc else name
                lines.append(shorten(display, width=60, placeholder="…"))
            lines.append("")
            lines.append(f"Page {page+1}/{total_pages}  radius={radius}")
            lines.append("[YEL] Prev  [GRN] Refresh  [BLU] Next")
        lines.append("docs: ebird")
        api.screen.display_text("\n".join(lines), font_size=18, align="left")
        set_nav_leds()

    def refresh_data():
        nonlocal sightings_cache, page, last_fetch
        try:
            sightings_cache = fetch_sightings(lat, lng, radius, api_key, timeout=request_timeout)
            total_pages = compute_pages()
            if page >= total_pages:
                page = total_pages - 1
        except Exception as e:
            sightings_cache = []
            api.screen.display_text(f"{title}\n\nErr: {e}", align="left")
        last_fetch = time.time()
        display_page()

    def on_button(event):
        nonlocal page
        btn = event.get("button")
        if btn == "green":
            refresh_data()
        elif btn == "yellow" and page > 0:
            page -= 1
            display_page()
        elif btn == "blue" and page < compute_pages() - 1:
            page += 1
            display_page()

    sub_ids.append(api.event_bus.subscribe("button_pressed", on_button))

    try:
        refresh_data()
        while not stop_event.is_set():
            if time.time() - last_fetch >= refresh_seconds:
                refresh_data()
            time.sleep(0.2)
    finally:
        for sid in sub_ids:
            api.event_bus.unsubscribe(sid)
        for c in ["red", "yellow", "green", "blue"]:
            api.hardware.set_led(c, False)
        api.screen.clear_screen()
