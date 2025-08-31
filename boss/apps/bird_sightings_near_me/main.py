"""Bird Sightings Near Me mini-app.

Displays recent nearby bird species using the eBird API (no auth for recent observations endpoint
with lat/long). Allows manual refresh with green button.
"""
from __future__ import annotations
from typing import Any, List
import time
from textwrap import shorten

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

API_URL_TMPL = "https://api.ebird.org/v2/data/obs/geo/recent?lat={lat}&lng={lng}&dist={radius}&back=7"
USER_AGENT = "BOSS-MiniApp/1.0"


def fetch_sightings(lat: float, lng: float, radius: int, timeout: float = 6.0) -> list[str] | None:
    if requests is None:
        return None
    url = API_URL_TMPL.format(lat=lat, lng=lng, radius=radius)
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    try:
        r = requests.get(url, timeout=timeout, headers=headers)
        if r.status_code == 200:
            data: List[dict[str, Any]] = r.json()
            species = []
            for entry in data[:12]:  # limit lines
                name = entry.get("comName") or entry.get("species") or entry.get("sciName")
                if name and name not in species:
                    species.append(name)
            return species
    except Exception:
        return None
    return None


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    lat = float(cfg.get("latitude", 51.5074))
    lng = float(cfg.get("longitude", -0.1278))
    radius = int(cfg.get("radius", 10))
    request_timeout = float(cfg.get("request_timeout_seconds", 6))
    refresh_seconds = float(cfg.get("refresh_seconds", 120))

    api.screen.clear_screen()
    title = "Nearby Birds"
    api.screen.display_text(title, font_size=22, align="center")
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show_sightings():
        species = fetch_sightings(lat, lng, radius, timeout=request_timeout)
        if not species:
            api.screen.display_text(f"{title}\n\n(no data / network error)", align="left")
            return
        lines = [title, ""] + [shorten(s, width=40, placeholder="…") for s in species[:10]]
        api.screen.display_text("\n".join(lines), align="left")

    def on_button(event):
        nonlocal last_fetch
        if event.get("button") == "green":
            last_fetch = time.time()
            show_sightings()

    sub_ids.append(api.event_bus.subscribe("button_pressed", on_button))

    try:
        show_sightings()
        last_fetch = time.time()
        while not stop_event.is_set():
            now = time.time()
            if now - last_fetch >= refresh_seconds:
                last_fetch = now
                show_sightings()
            time.sleep(0.2)
    finally:
        for sid in sub_ids:
            api.event_bus.unsubscribe(sid)
        for c in ["red", "yellow", "green", "blue"]:
            api.hardware.set_led(c, False)
        api.screen.clear_screen()
