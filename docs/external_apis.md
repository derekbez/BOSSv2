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
| AVIATIONSTACK_API_KEY | BOSS_APP_AVIATIONSTACK_API_KEY |
| NASA_API_KEY | BOSS_APP_NASA_API_KEY |
| IPGEO_API_KEY | BOSS_APP_IPGEO_API_KEY |
| WORDNIK_API_KEY | BOSS_APP_WORDNIK_API_KEY |
| (future legacy placeholders) | (add here) |

Action: create follow-up task to refactor apps to use only canonical names, then drop this section.

## 3. Service Registry
Add a row when adopting a new third‑party service (NOT for purely local data sources).

| Service ID | Description | Base URL | Canonical Env Var(s) | Rate Limit Notes | Test Command Example |
|------------|-------------|----------|----------------------|------------------|---------------------|
| openweather | Weather data | https://api.openweathermap.org | `BOSS_APP_WEATHER_API_KEY` | 60/min free tier | `curl "https://api.openweathermap.org/data/2.5/weather?q=London&appid=$BOSS_APP_WEATHER_API_KEY"` |
| aviationstack | Flights (real-time/historical) | http://api.aviationstack.com | `BOSS_APP_AVIATIONSTACK_API_KEY` | 500 req/mo (free) | `curl "http://api.aviationstack.com/v1/flights?access_key=$BOSS_APP_AVIATIONSTACK_API_KEY&limit=1"` |
| ebird | Recent bird observations | https://api.ebird.org | `BOSS_APP_EBIRD_API_KEY` (X-eBirdApiToken) | Undocumented (be conservative) | `curl -H "X-eBirdApiToken: $BOSS_APP_EBIRD_API_KEY" "https://api.ebird.org/v2/data/obs/geo/recent?lat=51.5074&lng=-0.1278&dist=5&maxResults=1"` |
| nasa | NASA datasets (APOD, etc.) | https://api.nasa.gov | `BOSS_APP_NASA_API_KEY` | Varies by endpoint | `curl "https://api.nasa.gov/planetary/apod?api_key=$BOSS_APP_NASA_API_KEY&count=1"` |
| ipgeolocation | Astronomy (sun/moon phase) | https://api.ipgeolocation.io | `BOSS_APP_IPGEO_API_KEY` | Free tier limited | `curl "https://api.ipgeolocation.io/astronomy?apiKey=$BOSS_APP_IPGEO_API_KEY&lat=51.5074&long=-0.1278"` |
| wordnik | Dictionary / word data | https://api.wordnik.com | `BOSS_APP_WORDNIK_API_KEY` | 1000 req/day | (see docs) |
| newsdata | News headlines | https://newsdata.io | `BOSS_APP_NEWSDATA_API_KEY` | 200 req/day | `curl "https://newsdata.io/api/1/news?apikey=$BOSS_APP_NEWSDATA_API_KEY&country=us&language=en"` |
| lastfm | Music metadata | https://ws.audioscrobbler.com | `BOSS_APP_LASTFM_API_KEY` | 5 req/sec | (see docs) |
| worldtides | Tide predictions | https://www.worldtides.info | `BOSS_APP_WORLDTIDES_API_KEY` | 4 req/hr (free) | (see docs) |

## 4. Per-App External Requirements (Merged)
Legend:
* Env Var: canonical preferred name (legacy name in parentheses if still used in code)
* Fallback: User-friendly text shown on screen when data unavailable

| App | API / Source | Env Var (canonical) | Auth Type | Header / Usage | Rate Limit (approx) | Fallback Behavior | Notes |
|-----|--------------|--------------------|-----------|----------------|--------------------|-------------------|-------|
| quote_of_the_day | Quotable / (They Said So optional) | (optional) `BOSS_APP_THEYSAIDSO_API_KEY` | Key (optional) | `X-Api-Key` | ~10/min (TheySaidSo) | "(error/no data)" | Currently using free Quotable (no key) |
| breaking_news | NewsData.io | `BOSS_APP_NEWSDATA_API_KEY` (legacy NEWSDATA_API_KEY) | Key (query param) | `?apikey=...` | 200 req/day | "(no news / network error)" | Consider alt provider later |
| flights_leaving_heathrow | Aviationstack | `BOSS_APP_AVIATIONSTACK_API_KEY` (legacy AVIATIONSTACK_API_KEY) | Key (query param) | `access_key` | 500 req/mo | "(no data / error)" | Share key w/ other flight app |
| flight_status_favorite_airline | Aviationstack | `BOSS_APP_AVIATIONSTACK_API_KEY` (legacy AVIATIONSTACK_API_KEY) | Key | `access_key` | 500 req/mo | "(no data / error)" | Deduplicate fetch interval |
| bird_sightings_near_me | eBird recent observations | `BOSS_APP_EBIRD_API_KEY` | Token header | `X-eBirdApiToken` | Be conservative | "(no data / network error)" | Consider geo restriction |
| word_of_the_day | Wordnik | `BOSS_APP_WORDNIK_API_KEY` (legacy WORDNIK_API_KEY) | Key | Query param | 1000 req/day | "(error/ no data)" | Cache 12h |
| moon_phase | ipgeolocation.io astronomy | `BOSS_APP_IPGEO_API_KEY` (legacy IPGEO_API_KEY) | Key | Query param | 1000 req/day | "(error/no data)" | Refresh 6h |
| today_in_music | Last.fm | `BOSS_APP_LASTFM_API_KEY` | Key | Query param | 5 req/sec | "(error/no data)" | Hourly refresh |
| space_update | NASA (APOD / Mars) | `BOSS_APP_NASA_API_KEY` (legacy NASA_API_KEY) | Key | Query param | 30 req/hr (DEMO lower) | "(error/no data)" or demo | Prefer real key |
| local_tide_times | WorldTides | `BOSS_APP_WORLDTIDES_API_KEY` | Key | Query param | 4 req/hr | "(error/no data)" | 3h refresh |
| dad_joke_generator | icanhazdadjoke | (none) | None | `Accept: application/json` | Light | "(network error)" | Add UA if throttled |
| joke_of_the_moment | JokeAPI | (none) | None | Query params | Generous | "(error/no data)" | Respect blacklist flags |
| name_that_animal | Zoo Animal API | (none) | None | n/a | Unspecified | "(error/no data)" | Basic JSON |
| color_of_the_day | ColourLovers | (none) | None | n/a | Low | "(network error)" | Cache daily |
| on_this_day | byabbe.se | (none) | None | n/a | Unspecified | "(no events / error)" | Half-day refresh |
| tiny_poem | Poemist | (none) | None | n/a | Unspecified | "(error/no data)" | 3h refresh |
| top_trending_search | Local backend (Google Trends) | (backend managed) | Depends | Internal | Local | "(no trend / error)" | Backend doc separately |
| internet_speed_check | speedtest-cli (future) | (none) | None | CLI | Tool-defined | Placeholder text | Pending real integration |
| public_domain_book_snippet | Local assets | (none) | None | n/a | n/a | "(no book files)" | Ensure assets present |
| random_local_place_name | Local assets | (none) | None | n/a | n/a | Built-in fallback list | Provide curated list |
| random_emoji_combo | Local assets | (none) | None | n/a | n/a | Built-in fallback list | Provide emoji.json |
| constellation_of_the_night | Placeholder/local dataset | (TBD future) | TBD | n/a | n/a | Static message | Placeholder state |

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
