# Configuration & Secrets

## Config Files
- Primary: `boss/config/boss_config.json` (strict JSON; no comments).
- App mappings (if used): `boss/config/app_mappings.json`.

## Models
- `BossConfig` → `hardware: HardwareConfig`, `system: SystemConfig`.
- Hardware fields: pins, screen dimensions, backend (`textual`), audio.
- System fields: timeouts, directories, logging, event bus sizing, webui flags.

## Loading Flow
1. `get_effective_config()` loads file.
2. Validates pin ranges, uniqueness, screen dimensions.
3. Applies env overrides.

## Environment Overrides
| Variable | Effect |
|----------|--------|
| `BOSS_CONFIG_PATH` | Alternate config file path |
| `BOSS_LOG_LEVEL` | Override log level |
| `BOSS_TEST_MODE=1` | Force mock hardware + DEBUG |
| `BOSS_DEV_MODE=1` | Enable webui + DEBUG |
| `BOSS_FORCE_HARDWARE` (future) | Force backend selection |

## Validation Rules (Summary)
- All required numeric pin fields present & unique.
- Screen width/height > 0.
- Log level ∈ {DEBUG, INFO, WARNING, ERROR, CRITICAL}.
- If invalid → startup abort with logged errors.

## Secrets Handling
- Stored in `secrets/` directory (e.g., `secrets.env`).
- Never commit actual secret values; provide sample file.
- Load via dedicated secrets manager (e.g., `secrets_manager.py`).
- Use environment variables for overrides in deployment.

## Adding New Config Fields
1. Add to JSON with safe default.
2. Extend dataclass in `boss/core/models/config.py`.
3. Adjust loader & validation rules.
4. Update this document + any tests.

## Anti-Patterns
| Issue | Why |
|-------|-----|
| JSON comments | Break strict loader |
| Silent fallback on invalid pins | Masks hardware misconfiguration |
| Embedding secrets into config | Risks accidental commit |

## Checklist Before Commit
- Config file parses without exceptions.
- No duplicate pins.
- Any new field has corresponding doc update.

Next: `web_ui_and_debugging.md`.
