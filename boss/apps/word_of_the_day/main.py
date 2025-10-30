"""Word of the Day mini-app.

Uses Wordnik API. Refresh infrequently (half-day) or manually.
"""
from __future__ import annotations
import time

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

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

API_URL = "https://api.wordnik.com/v4/words.json/wordOfTheDay"


def fetch_word(api_key: str | None, timeout: float = 6.0):
    if requests is None:
        raise RuntimeError("requests not available")
    params = {}
    if api_key:
        params["api_key"] = api_key
    r = requests.get(API_URL, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    word = data.get("word") or "?"
    defs = data.get("definitions", [{}])[0].get("text", "No definition.")
    example = data.get("examples", [{}])[0].get("text", "")
    return word, defs, example


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    # STRICT canonical secret only (2025-09-01): per-app config api_key or canonical secret
    from boss.config.secrets_manager import secrets
    api_key = cfg.get("api_key") or secrets.get("BOSS_APP_WORDNIK_API_KEY")
    refresh_seconds = float(cfg.get("refresh_seconds", 43200))
    timeout = float(cfg.get("request_timeout_seconds", 6))

    api.screen.clear_screen()
    title = "Word of the Day"
    api.screen.display_text(title, font_size=28, align="center")
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show():
        try:
            word, defs, example = fetch_word(api_key, timeout=timeout)
            defs_txt = defs  # no truncation; backend will wrap
            lines = [title, "", word, defs_txt]
            if example:
                lines.append("")
                lines.append("Ex: " + example)
            api.screen.display_text("\n".join(lines), align="left")
        except Exception as e:
            api.screen.display_text(f"{title}\n\nErr: {e}", align="left")

    def on_button(event_type, payload):
        nonlocal last_fetch
        if payload.get("button") == "green":
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
