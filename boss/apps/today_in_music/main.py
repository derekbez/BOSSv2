"""Today in Music mini-app.

Shows top track for a given tag using Last.fm API.
Refresh hourly or via green button.
"""
from __future__ import annotations
import time

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

API_URL = "http://ws.audioscrobbler.com/2.0/"


def fetch_track(api_key: str | None, tag: str, timeout: float = 6.0):
    if requests is None:
        return None
    params = {
        "method": "tag.gettoptracks",
        "tag": tag,
        "format": "json",
        "limit": 1,
    }
    if api_key:
        params["api_key"] = api_key
    try:
        r = requests.get(API_URL, params=params, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            track = (data.get("tracks", {}) or {}).get("track")
            if isinstance(track, list) and track:
                t0 = track[0]
                artist = (t0.get("artist") or {}).get("name") or "?"
                name = t0.get("name") or "?"
                return f"{artist} - {name}"
    except Exception:
        return None
    return None


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    api_key = cfg.get("api_key") or api.get_config_value("LASTFM_API_KEY")
    tag = cfg.get("tag", "rock")
    refresh_seconds = float(cfg.get("refresh_seconds", 3600))
    timeout = float(cfg.get("request_timeout_seconds", 6))

    api.screen.clear_screen()
    api.screen.write_line("Music Top", 0)
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show():
        api.screen.clear_body(start_line=1)
        line = fetch_track(api_key, tag, timeout=timeout)
        if not line:
            api.screen.write_wrapped("(error/no data)", start_line=2)
            return
        api.screen.write_line(line[: api.screen.width - 1], 2)

    def on_button(ev):
        nonlocal last_fetch
        if ev.get("button") == "green":
            last_fetch = time.time()
            show()

    sub_ids.append(api.event_bus.subscribe("button_pressed", on_button))

    try:
        show()
        last_fetch = time.time()
        while not stop_event.is_set():
            if time.time() - last_fetch >= refresh_seconds:
                last_fetch = time.time()
                show()
            time.sleep(0.5)
    finally:
        for sid in sub_ids:
            api.event_bus.unsubscribe(sid)
        api.hardware.set_led("green", False)
        api.screen.clear_screen()
