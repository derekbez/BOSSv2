# External API & Secrets Registry

Date: 2025-08-30
Status: Living document (add new services via PR)

This registry is the single source of truth for any external web API a mini‑app uses. Mini‑apps must not hardcode credentials or describe setup steps elsewhere (except a short pointer in their own README).

## 1. Conventions
| Item | Convention |
|------|------------|
| Per‑app secret env var name | `BOSS_APP_<APPNAME>_<PURPOSE>` (uppercase, no hyphen) |
| Global/shared secret | `BOSS_GLOBAL_<PURPOSE>` |
| Sample file | `secrets/secrets.sample.env` (committed) |
| Real secrets | `secrets/secrets.env` (NOT committed) or systemd `/etc/boss/secrets.env` |
| Loader precedence | Process env > local file entry > default passed by caller |
| Missing required secret | App should log error then abort early (graceful) |

## 2. Current Services
Add rows when adopting a new service.

| Service ID | Description | Base URL | Required Env Var(s) | Rate Limit Notes | Test Command Example |
|------------|-------------|----------|---------------------|------------------|---------------------|
| openweather | Weather data | https://api.openweathermap.org | `BOSS_APP_WEATHER_API_KEY` | 60/min free tier | `curl "https://api.openweathermap.org/data/2.5/weather?q=London&appid=$BOSS_APP_WEATHER_API_KEY"` |
| aviationstack | Real-time & historical flight data | http://api.aviationstack.com | `BOSS_APP_AVIATIONSTACK_API_KEY` | 500 req / mo free tier (check account) | `curl "http://api.aviationstack.com/v1/flights?access_key=$BOSS_APP_AVIATIONSTACK_API_KEY&limit=1"` |
| ebird | Recent bird observations | https://api.ebird.org | `BOSS_APP_EBIRD_API_KEY` (passed via X-eBirdApiToken header) | Rate limits undocumented (be conservative) | `curl -H "X-eBirdApiToken: $BOSS_APP_EBIRD_API_KEY" "https://api.ebird.org/v2/data/obs/geo/recent?lat=51.5074&lng=-0.1278&dist=5&maxResults=1"` |
| nasa | NASA public datasets (APOD, images, etc.) | https://api.nasa.gov | `BOSS_APP_NASA_API_KEY` | Varies by endpoint; stay within fair use | `curl "https://api.nasa.gov/planetary/apod?api_key=$BOSS_APP_NASA_API_KEY&count=1"` |
| ipgeolocation | Astronomy (sun/moon, phase, etc.) | https://api.ipgeolocation.io | `BOSS_APP_IPGEO_API_KEY` | Free tier limited (see dashboard) | `curl "https://api.ipgeolocation.io/astronomy?apiKey=$BOSS_APP_IPGEO_API_KEY&lat=51.5074&long=-0.1278"` |

## 3. Adding a New External API
1. Pick a service id (lowercase, underscores) e.g. `space_data`.
2. Add a row above with placeholder env var name(s).
3. Add sample env entries in `secrets/secrets.sample.env` with `CHANGE_ME` values.
4. Use the secret in your app ONLY through `os.getenv()` (or the provided `SecretsManager`).
5. Update your app `manifest.json` with:
```json
"external_apis": ["space_data"],
"required_env": ["BOSS_APP_SPACEDATA_API_KEY"]
```
6. In code: assert presence of secrets early; fail fast with a helpful log.

## 4. Secret Rotation (Personal Project Simple Flow)
1. Edit local `secrets/secrets.env` with new key alongside old one (e.g. NEW var name).
2. Push to Pi using `python scripts/sync_secrets.py push`.
3. Restart service (`sudo systemctl restart boss`).
4. Remove deprecated key after verifying logs / behaviour.

## 5. Security Notes (Right‑Sized)
* No secrets in git history; keep `secrets/secrets.env` out of commits.
* Pi copy stored at `/etc/boss/secrets.env` (chmod 600, root:root). Systemd unit uses `EnvironmentFile=`.
* For future stronger protection you can adopt encrypted age/gnupg file; design keeps that pluggable.

## 6. Example Mini‑App Snippet
```python
from boss.infrastructure.config.secrets_manager import secrets

API_KEY = secrets.get("BOSS_APP_WEATHER_API_KEY")
if not API_KEY:
    api.log_error("Missing weather API key (BOSS_APP_WEATHER_API_KEY); aborting app start")
    return
```

## 7. Validation Idea (Future)
On system startup, iterate loaded apps: if any `required_env` missing, publish `app_error` and exclude from selectable list (UX friendly). Not yet implemented.

---
End of document.
