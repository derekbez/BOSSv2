"""Flight Status for Favourite Airline mini-app.

Displays limited set of flights for chosen airline using Aviationstack.
"""
from __future__ import annotations
import time
from boss.config.secrets_manager import secrets

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

API_URL = "http://api.aviationstack.com/v1/flights"


def fetch_status(api_key: str | None, airline_iata: str, timeout: float = 6.0, limit: int = 6):
    if requests is None:
        return None
    params = {"airline_iata": airline_iata, "limit": limit}
    if api_key:
        params["access_key"] = api_key
    try:
        r = requests.get(API_URL, params=params, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            flights = data.get("data", [])
            lines = []
            for f in flights:
                code = (f.get("flight") or {}).get("iata") or "?"
                dep = (f.get("departure") or {}).get("scheduled") or "?"
                stat = f.get("flight_status") or "?"
                if dep and len(dep) >= 16:
                    dep = dep[11:16]
                lines.append(f"{code} {dep} {stat}")
                if len(lines) >= limit:
                    break
            return lines
    except Exception:
        return None
    return None


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    # STRICT canonical key only (2025-09-01): per-app config 'api_key' OR secrets canonical.
    api_key = cfg.get("api_key") or secrets.get("BOSS_APP_AVIATIONSTACK_API_KEY")
    airline_iata = cfg.get("iata", "BA")
    timeout = float(cfg.get("request_timeout_seconds", 6))
    refresh_seconds = float(cfg.get("refresh_seconds", 600))

    api.screen.clear_screen()
    title = f"Flights {airline_iata}"
    api.screen.display_text(title, font_size=22, align="center")
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show():
        if not api_key:
            api.screen.display_text(f"{title}\n\n(missing API key)", align="left")
            return
        lines = fetch_status(api_key, airline_iata, timeout=timeout)
        if not lines:
            api.log_warning("Airline status fetch returned no data")
            api.screen.display_text(f"{title}\n\n(no data / error)", align="left")
            return
        body = "\n".join(lines[:8])
        api.screen.display_text(f"{title}\n\n{body}", align="left")

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
