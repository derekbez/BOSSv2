"""Color of the Day mini-app.

Fetches a random color from ColourLovers (XML) and displays name + hex.
Refresh with green button; otherwise daily (very infrequent).
Falls back to local color data if API is unavailable.
"""
from __future__ import annotations
import json
import os
import random
import time
import xml.etree.ElementTree as ET

def _summarize_error(err: Exception) -> str:
    resp = getattr(err, 'response', None)
    if resp is not None and hasattr(resp, 'status_code'):
        try:
            reason = getattr(resp, 'reason', '') or ''
            msg = f"HTTP {resp.status_code} {reason}".strip()
        except Exception:
            msg = ''
    else:
        msg = str(err) or err.__class__.__name__
    if not msg:
        msg = err.__class__.__name__
    if len(msg) > 60:
        msg = msg[:57] + '...'
    return msg

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

API_URL = "https://www.colourlovers.com/api/colors/random?format=xml"
ASSET_FILE = "colors.json"


def load_local_colors(asset_dir: str):
    """Load color data from local assets, with hardcoded fallback."""
    path = os.path.join(asset_dir, ASSET_FILE)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Hardcoded fallback colors if assets not available
        return [
            {"title": "Ocean Blue", "hex": "006994"},
            {"title": "Sunset Orange", "hex": "FF6B35"},
            {"title": "Forest Green", "hex": "228B22"},
            {"title": "Royal Purple", "hex": "7851A9"},
            {"title": "Cherry Red", "hex": "DE3163"},
            {"title": "Golden Yellow", "hex": "FFD700"},
            {"title": "Sky Blue", "hex": "87CEEB"},
            {"title": "Coral Pink", "hex": "FF7F7F"},
            {"title": "Emerald Green", "hex": "50C878"},
            {"title": "Lavender", "hex": "E6E6FA"}
        ]


def fetch_color_from_api(timeout: float = 6.0):
    """Fetch color from ColourLovers API."""
    if requests is None:
        raise RuntimeError("requests not available")
    r = requests.get(API_URL, timeout=timeout, headers={"User-Agent": "BOSS-Color/1.0"})
    r.raise_for_status()
    root = ET.fromstring(r.text)
    color = root.find("color")
    if color is None:
        raise ValueError("No <color> element")
    title = (color.findtext("title") or "?").strip()
    hexcode = (color.findtext("hex") or "??????").strip()
    return title, hexcode


def fetch_color_from_local(asset_dir: str):
    """Fetch random color from local assets."""
    colors = load_local_colors(asset_dir)
    color = random.choice(colors)
    return color["title"], color["hex"]


def fetch_color(timeout: float = 6.0, asset_dir: str = None):
    """Fetch color from API, falling back to local data if API fails."""
    try:
        # Try API first
        return fetch_color_from_api(timeout)
    except Exception:
        # Fall back to local data if API fails
        if asset_dir is None:
            # This shouldn't happen in normal usage, but provide a safe fallback
            return "Fallback Blue", "0066CC"
        return fetch_color_from_local(asset_dir)


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    refresh_seconds = float(cfg.get("refresh_seconds", 86400))
    timeout = float(cfg.get("request_timeout_seconds", 6))

    # Get asset directory for fallback colors
    asset_dir = api.get_app_asset_path()

    api.screen.clear_screen()
    title = "Color of Day"
    api.screen.display_text(title, font_size=22, align="center")
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show_color():
        try:
            cname, hexcode = fetch_color(timeout=timeout, asset_dir=asset_dir)
            api.screen.display_text(f"{title}\n\n{cname}\n#{hexcode}", align="center")
        except Exception as e:
            api.screen.display_text(f"{title}\n\nErr: {_summarize_error(e)}", align="left")

    def on_button(ev):
        nonlocal last_fetch
        if ev.get("button") == "green":
            last_fetch = time.time()
            show_color()

    sub_ids.append(api.event_bus.subscribe("button_pressed", on_button))

    try:
        show_color()
        last_fetch = time.time()
        while not stop_event.is_set():
            now = time.time()
            if now - last_fetch >= refresh_seconds:
                last_fetch = now
                show_color()
            time.sleep(0.5)
    finally:
        for sid in sub_ids:
            api.event_bus.unsubscribe(sid)
        api.hardware.set_led("green", False)
        api.screen.clear_screen()
