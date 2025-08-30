"""Breaking News mini-app.

Fetches recent headlines periodically. Uses NewsData.io free tier.
Graceful errors and manual refresh via green button.
"""
from __future__ import annotations
from typing import Any
import time

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

API_URL = "https://newsdata.io/api/1/news"


def fetch_headlines(api_key: str | None, country: str, category: str, timeout: float = 6.0) -> list[str] | None:
    if requests is None:
        return None
    params = {
        "country": country,
        "category": category,
        "language": "en"
    }
    if api_key:
        params["apikey"] = api_key
    try:
        r = requests.get(API_URL, params=params, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            articles = data.get("results", [])
            heads = []
            for a in articles:
                title = a.get("title")
                if title:
                    heads.append(title[:80])
                if len(heads) >= 6:
                    break
            return heads
    except Exception:
        return None
    return None


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    api_key = cfg.get("api_key") or api.get_config_value("NEWS_API_KEY")
    country = cfg.get("country", "gb")
    category = cfg.get("category", "technology")
    refresh_seconds = float(cfg.get("refresh_seconds", 300))
    timeout = float(cfg.get("request_timeout_seconds", 6))

    api.screen.clear_screen()
    api.screen.write_line("Headlines", 0)
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show_news():
        api.screen.clear_body(start_line=1)
        heads = fetch_headlines(api_key, country, category, timeout=timeout)
        if not heads:
            api.screen.write_wrapped("(no news / network error)", start_line=2)
            return
        line = 2
        for h in heads:
            if line >= api.screen.height - 1:
                break
            api.screen.write_line(h[: api.screen.width - 1], line)
            line += 1

    def on_button(ev):
        nonlocal last_fetch
        if ev.get("button") == "green":
            last_fetch = time.time()
            show_news()

    sub_ids.append(api.event_bus.subscribe("button_pressed", on_button))

    try:
        show_news()
        last_fetch = time.time()
        while not stop_event.is_set():
            now = time.time()
            if now - last_fetch >= refresh_seconds:
                last_fetch = now
                show_news()
            time.sleep(0.25)
    finally:
        for sid in sub_ids:
            api.event_bus.unsubscribe(sid)
        api.hardware.set_led("green", False)
        api.screen.clear_screen()
