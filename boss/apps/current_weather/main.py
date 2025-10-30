"""current_weather - Periodic weather snapshot via Open-Meteo.

STRICT MODE (2025-09-01):
* Requires a valid GLOBAL system location (api.get_global_location must supply numeric latitude/longitude).
* No silent fallback to default coordinates. If missing -> display error & abort.
* Displays current weather plus next 8 hours (temp, wind, humidity, cloud, precipitation).
* Adds humidity and precipitation to current conditions view.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from threading import Event
import time

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # fallback handled at runtime


def fetch_weather(lat: float, lon: float, timeout: float) -> Dict[str, Any]:
    if requests is None:
        raise RuntimeError("requests not available")
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        # Request hourly variables for next hours summary
        "hourly": ",".join([
            "temperature_2m",
            "relativehumidity_2m",
            "precipitation",
            "cloudcover",
            "windspeed_10m"
        ]),
        "timezone": "auto"
    }
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def format_current(data: Dict[str, Any]) -> str:
    cw = data.get("current_weather", {}) if data else {}
    # Current weather block does not include humidity/precip; derive from hourly if available
    hourly = data.get("hourly", {}) if data else {}
    times: List[str] = hourly.get("time", []) or []
    hums: List[Optional[float]] = hourly.get("relativehumidity_2m", []) or []
    precs: List[Optional[float]] = hourly.get("precipitation", []) or []
    temp = cw.get("temperature")
    wind = cw.get("windspeed")
    cloud = cw.get("cloudcover") if "cloudcover" in cw else cw.get("cloud_cover")
    current_time = cw.get("time")
    hum = prec = None
    if current_time and current_time in times:
        idx = times.index(current_time)
        hum = hums[idx] if idx < len(hums) else None
        prec = precs[idx] if idx < len(precs) else None
    def fmt(v, suffix=""):
        return f"{v}{suffix}" if (v is not None and v != "") else "?"
    # Precip shown only if >0
    precip_str = f" {prec:.1f}mm" if isinstance(prec, (int, float)) and prec > 0 else ""
    return (
        f"Temp: {fmt(temp,'°C')}  Wind: {fmt(wind,' km/h')}\n"
        f"Hum: {fmt(hum,'%')}  Cloud: {fmt(cloud,'%')}{precip_str}"
    )


def format_next_hours(data: Dict[str, Any], hours: int = 8) -> str:
    hourly = data.get("hourly", {}) if data else {}
    times: List[str] = hourly.get("time", []) or []
    temps: List[Optional[float]] = hourly.get("temperature_2m", []) or []
    hums: List[Optional[float]] = hourly.get("relativehumidity_2m", []) or []
    precs: List[Optional[float]] = hourly.get("precipitation", []) or []
    clouds: List[Optional[float]] = hourly.get("cloudcover", []) or []
    wind: List[Optional[float]] = hourly.get("windspeed_10m", []) or []
    cw = data.get("current_weather", {}) or {}
    cur_time = cw.get("time")
    start_idx = 0
    if cur_time and cur_time in times:
        start_idx = times.index(cur_time) + 1  # start after current hour
    # Build hourly tokens
    lines: List[str] = []
    for i in range(start_idx, min(start_idx + hours, len(times))):
        t_iso = times[i]
        hour_label = t_iso.split("T")[-1][:5]  # HH:MM
        temp = temps[i] if i < len(temps) else None
        hum = hums[i] if i < len(hums) else None
        prec = precs[i] if i < len(precs) else None
        cld = clouds[i] if i < len(clouds) else None
        wnd = wind[i] if i < len(wind) else None
        # Compact token: HH T°C H% C% Pmm W
        token = f"{hour_label} {int(temp) if isinstance(temp,(int,float)) else '?'}° {int(hum) if isinstance(hum,(int,float)) else '?'}% {int(cld) if isinstance(cld,(int,float)) else '?'}%"
        if isinstance(prec, (int, float)) and prec > 0:
            token += f" {prec:.1f}mm"
        token += f" {int(wnd) if isinstance(wnd,(int,float)) else '?'}k"
        lines.append(token)
    if not lines:
        return "(no hourly)"
    return "\n".join(lines)


def run(stop_event: Event, api: Any) -> None:
    api.log_info("current_weather starting")
    cfg = api.get_app_config(default={}) or {}
    global_loc = api.get_global_location() if hasattr(api, "get_global_location") else None
    def _sleep_with_stop(seconds: float) -> None:
        end = time.time() + seconds
        while time.time() < end and not stop_event.wait(0.1):
            pass

    if not global_loc or global_loc.get("latitude") is None or global_loc.get("longitude") is None:
        api.screen.clear_screen()
        api.screen.display_text(
            "Weather Error:\nGlobal location not set. Configure system latitude/longitude.",
            align="center",
        )
        api.log_error("current_weather aborted: missing global location")
        # Be responsive to stop_event during brief display
        if hasattr(api, "sleep"):
            try:
                api.sleep(4)
            except Exception:
                _sleep_with_stop(4)
        else:
            _sleep_with_stop(4)
        return
    try:
        lat = float(global_loc.get("latitude"))  # type: ignore[arg-type]
        lon = float(global_loc.get("longitude"))  # type: ignore[arg-type]
    except Exception:
        api.screen.clear_screen()
        api.screen.display_text(
            "Weather Error:\nInvalid global location values (non-numeric).", align="center"
        )
        api.log_error("current_weather aborted: invalid global location numeric conversion")
        # Be responsive to stop_event during brief display
        if hasattr(api, "sleep"):
            try:
                api.sleep(4)
            except Exception:
                _sleep_with_stop(4)
        else:
            _sleep_with_stop(4)
        return
    refresh = int(cfg.get("refresh_seconds", 60))
    timeout = float(cfg.get("request_timeout_seconds", 4))

    def render_message(msg: str) -> None:
        api.screen.clear_screen()
        api.screen.display_text(msg, align="center")

    last_fetch_ok = False
    last_good_msg = ""

    while not stop_event.is_set():
        try:
            data = fetch_weather(lat, lon, timeout)
            msg = format_current(data)
            forecast_block = format_next_hours(data, hours=8)
            combined = msg + "\n-- Next 8h --\n" + forecast_block
            last_fetch_ok = True
            last_good_msg = combined
            render_message(combined)
        except Exception as e:
            api.log_error(f"Weather fetch failed: {e}")
            emsg = str(e)
            if not last_fetch_ok:
                render_message(f"Weather error:\n{emsg}")
            else:
                render_message(f"{last_good_msg}\nErr: {emsg}")
        # Wait in small increments to be responsive to stop_event
        slept = 0
        while slept < refresh and not stop_event.wait(0.5):
            slept += 0.5

    api.log_info("current_weather stopping")
