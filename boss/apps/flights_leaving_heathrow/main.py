"""Flights Leaving Heathrow mini-app.

Shows limited list of departing flights using Aviationstack API.
"""
from __future__ import annotations
import time
from typing import Any
from textwrap import shorten

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

API_URL = "http://api.aviationstack.com/v1/flights"


def fetch_flights(api_key: str | None, timeout: float = 6.0, limit: int = 8):
    if requests is None:
        return {"error": "requests library not available"}
    
    params = {"dep_iata": "LHR", "limit": limit}
    if api_key:
        params["access_key"] = api_key
    
    try:
        r = requests.get(API_URL, params=params, timeout=timeout)
        
        if r.status_code == 200:
            data = r.json()
            flights = data.get("data", [])
            lines = []
            for f in flights:
                airline = (f.get("airline") or {}).get("name") or "?"
                code = (f.get("flight") or {}).get("iata") or "?"
                sched = (f.get("departure") or {}).get("scheduled") or "?"
                if sched and len(sched) >= 16:
                    sched = sched[11:16]
                lines.append(f"{code} {sched} {airline}")
                if len(lines) >= limit:
                    break
            return lines if lines else {"error": "no flights found"}
        elif r.status_code == 401:
            return {"error": "authentication failed (check API key)"}
        elif r.status_code == 429:
            return {"error": "rate limit exceeded"}
        else:
            return {"error": f"API error (status {r.status_code})"}
            
    except requests.exceptions.ConnectionError:
        return {"error": "network connection failed"}
    except requests.exceptions.Timeout:
        return {"error": "request timeout"}
    except requests.exceptions.RequestException as e:
        return {"error": f"request failed: {str(e)[:50]}"}
    except Exception as e:
        return {"error": f"unexpected error: {str(e)[:50]}"}
    
    return {"error": "unknown error"}


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    # Support both canonical and legacy API key names
    api_key = (cfg.get("api_key") or 
               api.get_config_value("BOSS_APP_AVIATIONSTACK_API_KEY") or 
               api.get_config_value("AVIATIONSTACK_API_KEY"))
    timeout = float(cfg.get("request_timeout_seconds", 6))
    refresh_seconds = float(cfg.get("refresh_seconds", 600))

    api.screen.clear_screen()
    title = "LHR Departures"
    api.screen.display_text(title, font_size=22, align="center")
    api.hardware.set_led("green", True)

    sub_ids = []
    last_fetch = 0.0

    def show():
        result = fetch_flights(api_key, timeout=timeout)
        
        # Handle error responses
        if isinstance(result, dict) and "error" in result:
            error_msg = result["error"]
            if "authentication failed" in error_msg or "API key" in error_msg:
                display_msg = f"{title}\n\n(missing/invalid API key)"
            elif "network" in error_msg or "connection" in error_msg:
                display_msg = f"{title}\n\n(network error)"
            elif "timeout" in error_msg:
                display_msg = f"{title}\n\n(request timeout)"
            elif "rate limit" in error_msg:
                display_msg = f"{title}\n\n(rate limit exceeded)"
            else:
                display_msg = f"{title}\n\n(error: {error_msg})"
            api.screen.display_text(display_msg, align="left")
            return
        
        # Handle successful results
        if not result:
            api.screen.display_text(f"{title}\n\n(no data available)", align="left")
            return
            
        body = "\n".join(shorten(l, width=42, placeholder="…") for l in result[:8])
        api.screen.display_text(f"{title}\n\n{body}", align="left")

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
