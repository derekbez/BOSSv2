"""Live external fetch smoke tests for mini-app helper functions.

These are intentionally minimal: each test calls the app's fetch_* helper once
with sane parameters and asserts that some data structure (non-empty / not None)
is returned. They are skipped by default to avoid consuming free-tier quotas.

Enable by setting environment variable RUN_LIVE_FETCH_TESTS=1.

Per-function required API keys are checked; if missing the individual test is skipped.

NOTE: Keep timeouts small and limits low to conserve quota.
"""
from __future__ import annotations

import importlib
import os
import time
import datetime as _dt
import json
from pathlib import Path
import pytest

if os.getenv("RUN_LIVE_FETCH_TESTS") != "1":  # Gate entire module
    pytest.skip("Set RUN_LIVE_FETCH_TESTS=1 to run live fetch tests", allow_module_level=True)


def _get_global_location() -> tuple[float, float]:
    cfg_path = Path(__file__).parents[2] / "boss" / "config" / "boss_config.json"
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        loc = data.get("system", {}).get("location") or data.get("location")
        if loc and "latitude" in loc and "longitude" in loc:
            return float(loc["latitude"]), float(loc["longitude"])
    except Exception:
        pass
    # Fallback London
    return 51.5074, -0.1278


LAT, LON = _get_global_location()
TODAY = _dt.date.today()

# Test matrix: (module_path, function_name, args_builder, required_env_keys, description)
TEST_CASES = [
    ("boss.apps.word_of_the_day.main", "fetch_word", lambda: {"api_key": os.getenv("BOSS_APP_WORD_API_KEY"), "timeout": 5.0}, [], "word"),
    ("boss.apps.quote_of_the_day.main", "fetch_quote", lambda: {"timeout": 5.0}, [], "quote"),
    ("boss.apps.space_update.main", "fetch_space", lambda: {"api_key": os.getenv("BOSS_APP_NASA_API_KEY"), "timeout": 5.0}, ["BOSS_APP_NASA_API_KEY"], "space"),
    ("boss.apps.tiny_poem.main", "fetch_poem", lambda: {"timeout": 5.0}, [], "poem"),
    ("boss.apps.joke_of_the_moment.main", "fetch_joke", lambda: {"category": "Programming", "jtype": "single", "blacklist": [], "timeout": 5.0}, [], "joke single"),
    ("boss.apps.dad_joke_generator.main", "fetch_joke", lambda: {"timeout": 5.0}, [], "dad joke"),
    ("boss.apps.random_useless_fact.main", "fetch_fact", lambda: {"timeout": 5.0}, [], "fact"),
    ("boss.apps.color_of_the_day.main", "fetch_color", lambda: {"timeout": 5.0}, [], "color"),
    ("boss.apps.name_that_animal.main", "fetch_animal", lambda: {"timeout": 5.0}, [], "animal"),
    ("boss.apps.top_trending_search.main", "fetch_trend", lambda: {"url": "https://trends.google.com/trends/hottrends/visualize/internal/data/en-US", "timeout": 5.0}, [], "trending"),
    ("boss.apps.moon_phase.main", "fetch_data", lambda: {"api_key": os.getenv("BOSS_APP_IPGEO_API_KEY"), "lat": LAT, "lon": LON, "timeout": 6.0}, [], "moon"),
    ("boss.apps.current_weather.main", "fetch_weather", lambda: {"lat": LAT, "lon": LON, "timeout": 6.0}, [], "weather"),
    ("boss.apps.on_this_day.main", "fetch_events", lambda: {"month": TODAY.month, "day": TODAY.day, "timeout": 6.0}, [], "history events"),
    ("boss.apps.bird_sightings_near_me.main", "fetch_sightings", lambda: {"lat": LAT, "lng": LON, "radius": 10, "timeout": 6.0}, ["BOSS_APP_EBIRD_API_KEY"], "bird sightings"),
    ("boss.apps.breaking_news.main", "fetch_headlines", lambda: {"api_key": os.getenv("BOSS_APP_NEWSDATA_API_KEY"), "country": "us", "category": "technology", "timeout": 6.0}, ["BOSS_APP_NEWSDATA_API_KEY"], "news"),
    ("boss.apps.flight_status_favorite_airline.main", "fetch_status", lambda: {"api_key": os.getenv("BOSS_APP_AVIATIONSTACK_API_KEY"), "airline_iata": "BA", "timeout": 6.0, "limit": 2}, ["BOSS_APP_AVIATIONSTACK_API_KEY"], "flight status"),
    ("boss.apps.flights_leaving_heathrow.main", "fetch_flights", lambda: {"api_key": os.getenv("BOSS_APP_AVIATIONSTACK_API_KEY"), "timeout": 6.0, "limit": 3}, ["BOSS_APP_AVIATIONSTACK_API_KEY"], "flights"),
    ("boss.apps.local_tide_times.main", "fetch_tides", lambda: {"api_key": os.getenv("BOSS_APP_TIDES_API_KEY"), "lat": LAT, "lon": LON, "timeout": 6.0}, ["BOSS_APP_TIDES_API_KEY"], "tides"),
    ("boss.apps.today_in_music.main", "fetch_track", lambda: {"api_key": os.getenv("BOSS_APP_LASTFM_API_KEY"), "tag": "rock", "timeout": 6.0}, ["BOSS_APP_LASTFM_API_KEY"], "music"),
]


@pytest.mark.external
@pytest.mark.parametrize("module_path, func_name, args_builder, required_keys, label", TEST_CASES)
def test_fetch_function(module_path, func_name, args_builder, required_keys, label):
    # Skip if required key missing
    for k in required_keys:
        if not os.getenv(k):
            pytest.skip(f"Missing required env var {k} for {label}")

    try:
        mod = importlib.import_module(module_path)
    except Exception as e:  # pragma: no cover - import issue
        pytest.skip(f"Import failed for {module_path}: {e}")

    func = getattr(mod, func_name, None)
    if func is None:
        pytest.skip(f"Function {func_name} not present in {module_path}")

    args = args_builder() or {}
    # If api_key param exists and value is None, treat as optional and proceed.
    # Execute
    start = time.time()
    result = func(**args)
    duration = time.time() - start
    # Basic assertions: not None and not obviously empty (list/dict length > 0 or tuple truthy)
    if result is None:
        pytest.fail(f"{label} fetch returned None (args={args}) in {duration:.2f}s")
    if isinstance(result, (list, tuple, set, dict)) and len(result) == 0:
        pytest.fail(f"{label} fetch returned empty structure (args={args}) in {duration:.2f}s")
    # Duration guard (sanity, not a strict perf benchmark)
    assert duration < 15, f"{label} fetch took too long: {duration:.2f}s"

    # Light rate limiting: tiny sleep to avoid hammering APIs when parametrized
    time.sleep(0.15)
