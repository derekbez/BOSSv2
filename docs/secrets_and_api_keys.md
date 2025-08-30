# Secrets & External API Keys Management

Date: 2025-08-30
Status: Authoritative guide (supplements `external_apis.md` registry)

This document explains the practical workflow for adding, storing, syncing, rotating, and troubleshooting API keys and other sensitive values for B.O.S.S. mini‑apps across Windows development and the Raspberry Pi production device.

## 1. Goals
* Keep secrets out of git history.
* Single, predictable load path for all processes (systemd + local dev).
* Fast first‑time provisioning (idempotent, no manual mkdir on Pi).
* Clear naming to avoid collisions.
* Easy future upgrade to encrypted storage without breaking apps.

## 2. File & Load Locations
| Environment | Primary Secrets File | Loader Precedence | Notes |
|-------------|----------------------|-------------------|-------|
| Windows Dev | `secrets/secrets.env` | Process env > file | File is git‑ignored; create from sample |
| Raspberry Pi | `/etc/boss/secrets.env` | Process env > file | Owned by root:root, chmod 600, referenced by systemd `EnvironmentFile=` |

`boss.infrastructure.config.secrets_manager.SecretsManager` handles loading (lazy). You can also rely on `os.getenv` directly—just keep names consistent.

## 3. Naming Conventions
| Type | Pattern | Example |
|------|---------|---------|
| Per‑app secret | `BOSS_APP_<APPNAME>_<PURPOSE>` | `BOSS_APP_AVIATIONSTACK_API_KEY` |
| Global/shared | `BOSS_GLOBAL_<PURPOSE>` | `BOSS_GLOBAL_MAPBOX_TOKEN` |

Rules:
1. Uppercase only A–Z, digits, underscore.
2. `<APPNAME>` matches the manifest logical app domain (not necessarily directory, but keep aligned).
3. `<PURPOSE>` is short and descriptive (API_KEY, TOKEN, SECRET, KEY, CLIENT_ID, etc.).

## 4. Adding a New External API
1. Register it in `docs/external_apis.md` (new row + description).
2. Add placeholder to `secrets/secrets.sample.env` using `CHANGE_ME` value.
3. Add to the app manifest fields:
```json
"external_apis": ["<service_id>"],
"required_env": ["BOSS_APP_<APPNAME>_<PURPOSE>"]
```
4. In app code obtain the value:
```python
from boss.infrastructure.config.secrets_manager import secrets
API_KEY = secrets.get("BOSS_APP_MYAPP_API_KEY")
if not API_KEY:
    api.log_error("Missing API key; aborting")
    return
```
5. Fail fast (log + return) if critical secret missing.

## 5. Creating & Editing Local Secrets (Windows)
1. Copy sample: `copy secrets\secrets.sample.env secrets\secrets.env` (CMD) or `cp` in PowerShell.
2. Fill values (never quote unless value contains spaces; no trailing spaces).
3. (Optional) Persist individual vars outside file: `setx BOSS_APP_WEATHER_API_KEY <value>` (keeps them in user registry). File still overrides for simplicity.
4. Avoid accidental commits—`secrets.env` is already in `.gitignore`.

## 6. First-Time Provisioning on Raspberry Pi
1. Ensure SSH key auth (see `remote_development.md`).
2. Ensure your local `secrets/secrets.env` is ready.
3. Push (auto-creates `/etc/boss` if missing):
```
python scripts/sync_secrets.py push --host <pi>
```
4. Confirm hashes:
```
python scripts/sync_secrets.py verify --host <pi>
```
5. (One-time) Confirm systemd unit has: `EnvironmentFile=/etc/boss/secrets.env`.
6. Restart service:
```
sudo systemctl restart boss
```
7. Follow logs for any missing secret errors:
```
sudo journalctl -u boss -n 50 | grep -i missing
```

## 7. Sync Operations
| Operation | Command | What It Does | Safe If First Time? |
|-----------|---------|--------------|---------------------|
| Push | `python scripts/sync_secrets.py push --host <pi>` | Stages to /tmp, installs in /etc/boss with secure perms | Yes |
| Pull | `python scripts/sync_secrets.py pull --host <pi>` | Reads remote file via sudo cat to local path | Yes (fails if remote missing) |
| Verify | `python scripts/sync_secrets.py verify --host <pi>` | Compares local & remote SHA-256 | Yes (remote must exist) |

## 8. Rotation Procedure
1. Update local value in `secrets.env`.
2. Push + verify.
3. Restart service.
4. Observe logs; if stable remove any deprecated vars.

## 9. Multi-Developer Collaboration
* Each dev maintains their own `secrets.env`.
* Share new variable names through PR modifying `secrets.sample.env` & `external_apis.md`—never share values in PR.
* Optional secure channel to transmit actual values (Signal, 1Password vault, etc.).

## 10. Troubleshooting
| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| App marked ERROR missing secret | `required_env` not satisfied | Add key locally + push; restart |
| `verify` shows DIFF | Local edits not pushed or remote stale | Push again, confirm success |
| Push fails `scp: /tmp/... Permission denied` | Unusual remote /tmp perms | Fix remote /tmp permissions or change stage path |
| Service not seeing new value | Service not restarted | `sudo systemctl restart boss` |
| Value blank at runtime | Trailing spaces or Windows CRLF in file | Use UTF-8 LF; remove extra spaces |

## 11. Security Notes & Future Enhancements
Current posture is proportionate for hobby/low-risk: single root-owned file. Future options:
* Encrypted secrets file (age/gnupg) + decryption at boot.
* Hashicorp Vault / AWS SSM (add retrieval client before app start).
* Automatic `app_error` event emission & exclusion from selection list (planned idea).

## 12. Format Rules for `secrets.env`
* One VAR=VALUE per line.
* Lines starting with `#` ignored.
* No inline comments after value (keeps parsing trivial).
* Blank lines allowed.

Example:
```
# Weather
BOSS_APP_WEATHER_API_KEY=abcdef123456

# Flights
BOSS_APP_AVIATIONSTACK_API_KEY=pk_live_CHANGE_ME
```

## 13. Validation Script (Optional Future)
A potential enhancement: script to list missing `required_env` for all manifests and exit non‑zero (useful for CI). Not yet implemented.

---
End of document.
