"""Breaking News mini-app.

Fetches recent headlines periodically. Uses NewsData.io free tier.
Graceful errors and manual refresh via green button.
"""
from __future__ import annotations
from typing import Any
import os
from boss.infrastructure.config.secrets_manager import secrets
import time
from textwrap import shorten  # retained if user later toggles truncation (will remove if fully unused)

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

API_URL = "https://newsdata.io/api/1/news"


def fetch_headlines(api_key: str | None, country: str, category: str, timeout: float = 6.0, retries: int = 0, backoff: float = 1.5) -> list[str]:
    if requests is None:
        raise RuntimeError("requests not available")
    params = {"country": country, "category": category, "language": "en"}
    if api_key:
        params["apikey"] = api_key
    attempt = 0
    last_exc: Exception | None = None
    data = {}
    while attempt <= retries:
        try:
            r = requests.get(API_URL, params=params, timeout=timeout)
            if r.status_code == 401 and not api_key:
                raise RuntimeError("401 Unauthorized (missing NewsData API key). Set BOSS_APP_NEWSDATA_API_KEY or manifest config 'api_key'.")
            r.raise_for_status()
            data = r.json()
            break
        except requests.exceptions.ReadTimeout as e:  # type: ignore[attr-defined]
            last_exc = e
            if attempt >= retries:
                raise RuntimeError(f"Read timeout after {timeout}s (attempt {attempt+1}); increase request_timeout_seconds or reduce category scope.") from e
        except requests.exceptions.ConnectTimeout as e:  # type: ignore[attr-defined]
            last_exc = e
            if attempt >= retries:
                raise RuntimeError(f"Connect timeout after {timeout}s (attempt {attempt+1}); check network connectivity.") from e
        except Exception as e:
            last_exc = e
            if attempt >= retries:
                raise
        attempt += 1
        if attempt <= retries:
            time.sleep(backoff * attempt)
    if last_exc:
        # Should have been raised earlier; safeguard
        raise last_exc
    articles = data.get("results", [])
    heads: list[str] = []
    for a in articles:
        title = a.get("title")
        if title:
            heads.append(title[:80])
        if len(heads) >= 6:
            break
    if not heads:
        raise ValueError("No headlines")
    return heads


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    api_key = (
        cfg.get("api_key")
        or secrets.get("BOSS_APP_NEWSDATA_API_KEY")
        or secrets.get("NEWSDATA_API_KEY")  # legacy/raw fallback
        or os.environ.get("BOSS_APP_NEWSDATA_API_KEY")  # process env (if exported)
        or os.environ.get("NEWSDATA_API_KEY")
        or api.get_config_value("NEWSDATA_API_KEY")
    )
    country = cfg.get("country", "gb")
    category = cfg.get("category", "technology")
    refresh_seconds = float(cfg.get("refresh_seconds", 300))
    timeout = float(cfg.get("request_timeout_seconds", 6))
    retries = int(cfg.get("retries", 1))
    backoff = float(cfg.get("retry_backoff_seconds", 1.5))

    api.screen.clear_screen()
    title = "Headlines"
    api.screen.display_text(title, font_size=22, align="center")
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show_news():
        try:
            heads = fetch_headlines(api_key, country, category, timeout=timeout, retries=retries, backoff=backoff)
            # Show full headline text; allow UI to wrap naturally
            body = "\n".join(heads[:8])
            api.screen.display_text(f"{title}\n\n{body}", align="left")
        except Exception as e:
            api.screen.display_text(f"{title}\n\nErr: {e}", align="left")

    def on_button(event_type: str, payload: dict):
        nonlocal last_fetch
        if payload.get("button") == "green":
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
