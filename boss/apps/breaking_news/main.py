"""Breaking News mini-app.

Fetches recent headlines periodically. Uses NewsData.io free tier.
Graceful errors and manual refresh via green button.
"""
from __future__ import annotations
from typing import Any
from boss.infrastructure.config.secrets_manager import secrets
from boss.presentation.text.utils import TextPaginator, wrap_plain, estimate_char_columns
import time

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
    # STRICT canonical key only (2025-09-01): per-app config 'api_key' OR secrets canonical.
    api_key = cfg.get("api_key") or secrets.get("BOSS_APP_NEWSDATA_API_KEY")
    country = cfg.get("country", "gb")
    category = cfg.get("category", "technology")
    refresh_seconds = float(cfg.get("refresh_seconds", 300))
    timeout = float(cfg.get("request_timeout_seconds", 6))
    retries = int(cfg.get("retries", 1))
    backoff = float(cfg.get("retry_backoff_seconds", 1.5))

    api.screen.clear_screen()
    title = "Headlines"
    api.screen.display_text(title, font_size=22, align="center")
    # Green LED indicates a manual refresh is AVAILABLE (cooldown elapsed). Start off.
    api.hardware.set_led("green", False)

    sub_ids = []
    last_fetch = 0.0

    # Prepare paginator (will be filled after first fetch)
    cols = api.screen.estimate_columns() if hasattr(api.screen, 'estimate_columns') else estimate_char_columns(api.screen.width_px if hasattr(api.screen, 'width_px') else 800)
    per_page = max(6, (api.screen.height_lines // 2) if hasattr(api.screen, 'height_lines') else 6)
    paginator = TextPaginator([], per_page, led_update=lambda color, on: api.hardware.set_led(color, on))

    def show_news():
        try:
            heads = fetch_headlines(api_key, country, category, timeout=timeout, retries=retries, backoff=backoff)
            lines: list[str] = []
            for h in heads:
                lines.extend(wrap_plain(h, cols))
            paginator.set_lines(lines)
            page_text = "\n".join(paginator.page_lines())
            api.screen.display_text(f"{title}\n\n{page_text}", align="left")
        except Exception as e:
            api.screen.display_text(f"{title}\n\nErr: {e}", align="left")
        update_led()

    def update_led():
        ready = (time.time() - last_fetch) >= refresh_seconds
        api.hardware.set_led("green", ready)

    def on_button(event_type, payload):
        nonlocal last_fetch
        button = payload.get("button")
        if button == "green" and (time.time() - last_fetch) >= refresh_seconds:
            last_fetch = time.time()
            show_news()
        elif button == "yellow":
            if paginator.prev():
                api.screen.display_text(f"{title}\n\n" + "\n".join(paginator.page_lines()), align="left")
        elif button == "blue":
            if paginator.next():
                api.screen.display_text(f"{title}\n\n" + "\n".join(paginator.page_lines()), align="left")

    sub_ids.append(api.event_bus.subscribe("button_pressed", on_button))

    try:
        show_news()
        last_fetch = time.time()
        update_led()
        while not stop_event.is_set():
            now = time.time()
            if now - last_fetch >= refresh_seconds:
                last_fetch = now
                show_news()
            else:
                update_led()
            time.sleep(0.25)
    finally:
        for sid in sub_ids:
            api.event_bus.unsubscribe(sid)
        api.hardware.set_led("green", False)
        api.screen.clear_screen()
