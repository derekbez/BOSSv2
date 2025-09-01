# External API & Secrets Registry (GOLDEN SOURCE)

Date: 2025-08-30 (merged)
Status: Living document (single authoritative reference). supersedes former `miniapps_external_requirements.md` (now archived in `docs/archive/`).

This document is the single source of truth for:
* External web services used by mini‑apps (service-level registry)
* Per‑app external requirements (env vars, rate limits, fallback UX)
* Naming conventions and migration notes

> NOTE: Some existing app code still references legacy (unprefixed) environment variable names (e.g. `AVIATIONSTACK_API_KEY`). The canonical naming going forward uses the `BOSS_APP_` prefix. Until code is fully migrated, ensure BOTH names are present for affected keys in environments (or add a small compatibility lookup). See the Transitional Mapping section below.

## 1. Conventions
| Item | Convention |
|------|------------|
| Per‑app secret env var name (canonical) | `BOSS_APP_<SERVICE>_API_KEY` or `_API_TOKEN` |
| Global/shared secret | `BOSS_GLOBAL_<PURPOSE>` |
| Sample file | `secrets/secrets.sample.env` (committed) |
| Real secrets | Local: `secrets/secrets.env` (gitignored); Prod: systemd `/etc/boss/secrets.env` |
| Loader precedence | Process env > local file entry > default provided |
| Missing required secret | App logs error and aborts early (graceful) |
| Network timeout guidance | ≤ 6s per request |

## 2. Transitional Env Var Mapping (to remove after migration)
| Legacy (used in code today) | Canonical Prefixed Form |
|----------------------------|-------------------------|
| AVIATIONSTACK_API_KEY | BOSS_APP_AVIATIONSTACK_API_KEY (migration COMPLETE – legacy no longer referenced in code) |
| NASA_API_KEY | BOSS_APP_NASA_API_KEY |
| IPGEO_API_KEY | BOSS_APP_IPGEO_API_KEY |
| WORDNIK_API_KEY | BOSS_APP_WORDNIK_API_KEY |
| (future legacy placeholders) | (add here) |

Action: create follow-up task to refactor apps to use only canonical names, then drop this section.

## 3. Service Registry
Add a row when adopting a new third‑party service (NOT for purely local data sources). Reformatted to YAML for plain‑text readability.

```yaml
services:
    - id: openweather
        description: Weather data
        site: https://openweathermap.org
        base_api: https://api.openweathermap.org
        env: BOSS_APP_WEATHER_API_KEY
        rate_limit: "60/min free tier"
        test: curl "https://api.openweathermap.org/data/2.5/weather?q=London&appid=$BOSS_APP_WEATHER_API_KEY"
    - id: aviationstack
        description: Flights (real-time/historical)
        site: https://aviationstack.com
        base_api: http://api.aviationstack.com
        env: BOSS_APP_AVIATIONSTACK_API_KEY
        rate_limit: "500 req/mo (free)"
        test: curl "http://api.aviationstack.com/v1/flights?access_key=$BOSS_APP_AVIATIONSTACK_API_KEY&limit=1"
    - id: ebird
        description: Recent bird observations
        docs: https://documenter.getpostman.com/view/664302/S1ENwy59
        site: https://ebird.org
        base_api: https://api.ebird.org
        env: BOSS_APP_EBIRD_API_KEY
        auth_header: X-eBirdApiToken
        rate_limit: "Undocumented (be conservative)"
        test: curl -H "X-eBirdApiToken: $BOSS_APP_EBIRD_API_KEY" "https://api.ebird.org/v2/data/obs/geo/recent?lat=51.5074&lng=-0.1278&dist=5&maxResults=1"
    - id: nasa
        description: NASA datasets (APOD, Mars, etc.)
        site: https://www.nasa.gov
        base_api: https://api.nasa.gov
        env: BOSS_APP_NASA_API_KEY
        rate_limit: "Varies by endpoint"
        test: curl "https://api.nasa.gov/planetary/apod?api_key=$BOSS_APP_NASA_API_KEY&count=1"
    - id: ipgeolocation
        description: Astronomy (sun/moon phase)
        site: https://ipgeolocation.io
        base_api: https://api.ipgeolocation.io
        env: BOSS_APP_IPGEO_API_KEY
        rate_limit: "Free tier limited"
        test: curl "https://api.ipgeolocation.io/astronomy?apiKey=$BOSS_APP_IPGEO_API_KEY&lat=51.5074&long=-0.1278"
    - id: wordnik
        description: Dictionary / word data
        site: https://www.wordnik.com
        base_api: https://api.wordnik.com
        env: BOSS_APP_WORDNIK_API_KEY
        rate_limit: "1000 req/day"
    - id: newsdata
        description: News headlines
        site: https://newsdata.io
        base_api: https://newsdata.io
        env: BOSS_APP_NEWSDATA_API_KEY
        rate_limit: "200 req/day"
        test: curl "https://newsdata.io/api/1/news?apikey=$BOSS_APP_NEWSDATA_API_KEY&country=us&language=en"
    - id: lastfm
        description: Music metadata
        site: https://www.last.fm
        base_api: https://ws.audioscrobbler.com
        env: BOSS_APP_LASTFM_API_KEY
        rate_limit: "5 req/sec"
    - id: worldtides
        description: Tide predictions
        site: https://www.worldtides.info
        base_api: https://www.worldtides.info
        env: BOSS_APP_WORLDTIDES_API_KEY
        rate_limit: "4 req/hr (free)"
```

## 4. Per-App External Requirements (Merged)
Legend:
* Env Var: canonical preferred name (legacy name in parentheses if still used in code)
* Fallback: User-friendly text shown on screen when data unavailable

```yaml
apps_requirements:
    - app: quote_of_the_day
        api: quotable (They Said So optional)
        env: BOSS_APP_THEYSAIDSO_API_KEY (optional)
        auth: "Key (optional) via X-Api-Key"
        rate_limit: "~10/min (TheySaidSo)"
        fallback: "(error/no data)"
        notes: Free Quotable endpoint needs no key
    - app: breaking_news
        api: newsdata
        env: BOSS_APP_NEWSDATA_API_KEY (legacy NEWSDATA_API_KEY)
        auth: "Key query param ?apikey=..."
        rate_limit: "200 req/day"
        fallback: "(no news / network error)"
        notes: Consider alternative provider later
    - app: flights_leaving_heathrow
        api: aviationstack
        env: BOSS_APP_AVIATIONSTACK_API_KEY
        auth: "Key query param access_key"
        rate_limit: "500 req/mo"
        fallback: "(no data / error)"
        notes: Shares key with other flight app
    - app: flight_status_favorite_airline
        api: aviationstack
        env: BOSS_APP_AVIATIONSTACK_API_KEY
        auth: "Key query param access_key"
        rate_limit: "500 req/mo"
        fallback: "(no data / error)"
        notes: Deduplicate fetch interval
    - app: bird_sightings_near_me
        api: ebird
        env: BOSS_APP_EBIRD_API_KEY
        auth: "Token header X-eBirdApiToken"
        rate_limit: conservative
        fallback: "(no data / network error)"
        notes: Consider geo restriction
    - app: word_of_the_day
        api: wordnik
        env: BOSS_APP_WORDNIK_API_KEY (legacy WORDNIK_API_KEY)
        auth: "Key query param"
        rate_limit: "1000 req/day"
        fallback: "(error/no data)"
        notes: Cache 12h
    - app: moon_phase
        api: ipgeolocation
        env: BOSS_APP_IPGEO_API_KEY (legacy IPGEO_API_KEY)
        auth: "Key query param"
        rate_limit: "1000 req/day"
        fallback: "(error/no data)"
        notes: Refresh 6h
    - app: today_in_music
        api: lastfm
        env: BOSS_APP_LASTFM_API_KEY
        auth: "Key query param"
        rate_limit: "5 req/sec"
        fallback: "(error/no data)"
        notes: Hourly refresh
    - app: space_update
        api: nasa
        env: BOSS_APP_NASA_API_KEY (legacy NASA_API_KEY)
        auth: "Key query param"
        rate_limit: "30 req/hr (demo lower)"
        fallback: "(error/no data) or demo"
        notes: Prefer real key
    - app: local_tide_times
        api: worldtides
        env: BOSS_APP_WORLDTIDES_API_KEY
        auth: "Key query param"
        rate_limit: "4 req/hr"
        fallback: "(error/no data)"
        notes: Refresh 3h
    - app: dad_joke_generator
        api: icanhazdadjoke
        env: none
        auth: "None (Accept: application/json)"
        rate_limit: light
        fallback: "(network error)"
        notes: Add UA if throttled
    - app: joke_of_the_moment
        api: jokeapi
        env: none
        auth: None
        rate_limit: generous
        fallback: "(error/no data)"
        notes: Respect blacklist flags
    - app: name_that_animal
        api: zoo_animal_api
        env: none
        auth: None
        rate_limit: unspecified
        fallback: "(error/no data)"
        notes: Basic JSON
    - app: color_of_the_day
        api: colourlovers
        env: none
        auth: None
        rate_limit: low
        fallback: "(network error)"
        notes: Cache daily
    - app: on_this_day
        api: byabbe.se
        env: none
        auth: None
        rate_limit: unspecified
        fallback: "(no events / error)"
        notes: Half-day refresh
    - app: tiny_poem
        api: poemist
        env: none
        auth: None
        rate_limit: unspecified
        fallback: "(error/no data)"
        notes: Refresh 3h
    - app: top_trending_search
        api: internal_google_trends_backend
        env: backend managed
        auth: internal
        rate_limit: local
        fallback: "(no trend / error)"
        notes: Backend documented separately
    - app: internet_speed_check
        api: speedtest_cli (future)
        env: none
        auth: None
        rate_limit: tool-defined
        fallback: "Placeholder text"
        notes: Pending real integration
    - app: public_domain_book_snippet
        api: local_assets
        env: none
        auth: None
        rate_limit: n/a
        fallback: "(no book files)"
        notes: Ensure assets present
    - app: random_local_place_name
        api: local_assets
        env: none
        auth: None
        rate_limit: n/a
        fallback: built-in list
        notes: Provide curated list
    - app: random_emoji_combo
        api: local_assets
        env: none
        auth: None
        rate_limit: n/a
        fallback: built-in list
        notes: Provide emoji.json
    - app: constellation_of_the_night
        api: placeholder_dataset
        env: TBD
        auth: TBD
        rate_limit: n/a
        fallback: Static message
        notes: Placeholder state
```

## 5. Implementation Guidelines
1. Always set an explicit timeout (<= 6s) on network calls.
2. Provide concise, user-friendly fallback text; never show raw tracebacks on screen.
3. Respect documented refresh intervals to stay within rate limits (see table).
4. Cache where appropriate (word_of_the_day, tides, moon_phase, NASA daily endpoints).
5. For header auth (eBird) use the exact header key.
6. Don’t raise inside main loop; catch, log, fallback.

## 6. Fallback & Offline Strategy
* If env var absent and a public demo key exists (NASA), optionally try the demo key; otherwise display fallback text.
* (Future) Consider exponential backoff after repeated failures to reduce log noise & API usage.

## 7. Example Mini‑App Snippet
```python
from boss.infrastructure.config.secrets_manager import secrets

API_KEY = secrets.get("BOSS_APP_WEATHER_API_KEY")  # canonical
if not API_KEY:
    api.log_error("Missing weather API key; aborting app start")
    return
```

## 8. Adding a New External API (Process)
1. Choose a service id (lowercase) e.g. `space_data`.
2. Add to Service Registry table.
3. Add canonical env var to `secrets/secrets.sample.env` with `CHANGE_ME`.
4. Update target app `manifest.json` with `external_apis` + `required_env`.
5. Implement app code using `secrets.get(<VAR>)` and early validation.
6. Update Per-App table above with fallback behaviour.

## 9. Secret Rotation (Simple Flow)
1. Update local `secrets/secrets.env` with new value.
2. Push to Pi: `python scripts/sync_secrets.py push`.
3. Restart: `sudo systemctl restart boss`.
4. Remove old key after verification.

## 10. Security Notes (Right‑Sized)
* Never commit real secrets.
* Production secrets file: `/etc/boss/secrets.env` (chmod 600, root:root).
* Future hardening (optional): encrypted secrets file with age/gnupg; design remains pluggable.

## 11. Validation Checklist (Per API App)
Use when reviewing or adding an app:
* [ ] Manifest has `requires_network: true`.
* [ ] Timeout set on every `requests` call.
* [ ] Fallback text path exercised (tested or simulated).
* [ ] LED/button usage adheres to parity pattern (if interactive).
* [ ] No direct `requests` usage without explicit `timeout=`.
* [ ] Import guard uses standard pattern:
```python
try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore
    # (Future enhancement: central warning log if missing)
```
If `requests` is None the fetch helper returns `None`; ensure dependency installed via `pip install -r requirements/base.txt`.
* [ ] Uses canonical env var name (or transitional mapping documented) and present in sample env.

## 12. Future Improvements
* Remove transitional mapping after code refactor.
* Introduce automated startup validator that emits `app_error` and filters apps missing required secrets.
* Provide shared truncation/wrapping utility for long API responses.

---
End of golden source document.
