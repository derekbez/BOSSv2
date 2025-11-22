# Mini-App Blueprint (B.O.S.S.)

Authoritative specification for designing, implementing, and maintaining BOSS mini-apps. This extends `app_authoring.md` with enforceable standards.

## 1. Purpose & Scope
Provide uniform lifecycle, resource usage, hardware parity, event discipline, and clean shutdown patterns ensuring all apps are composable, observable, and safe.

## 2. Required Directory Structure
```
apps/<app_name>/
  manifest.json      # Required (see schema)
  main.py            # Required: defines run(stop_event, api)
  assets/            # Optional: images, sounds, small data files
```
No additional python packages or nested modules unless explicitly justified.

## 3. Manifest Specification (Schema)
Required fields:
- name: string (unique mini-app identifier; matches directory)
- description: short human-readable summary
- version: semantic version string (e.g. "1.0.0")
- author: contributor or team name

Optional / recommended fields:
- entry_point: defaults to "main.py"
- timeout_seconds: integer (override of global default)
- timeout_behavior: one of ["return", "rerun", "none"]
  - return: stop and transition to startup/idle
  - rerun: auto relaunch after cooldown (adds manifest key `timeout_cooldown_seconds`, default 1s)
  - none: disable timeout (discouraged except admin or diagnostic)
- tags: array of classification tags (MANDATORY – see Tag Taxonomy)
- requires_network: boolean (true if network calls are core)
- requires_audio: boolean (true if app plays sound)
- external_apis: list of registry IDs defined in `docs/external_apis.md`
- required_env: list of environment variable names the app expects
- config: object (app-specific runtime parameters; structure is free-form; validator will accept any JSON object)

Deprecated fields (reject in new manifests; migrate legacy apps):
- id: replaced by `name`
- title: replaced by `description`
- assets_required: documentation only; no enforcement
- api_keys: secrets should be in environment variables or secrets.env
- instructions: move to app README or remove

Future reserved (do not add ad-hoc keys): `permissions`, `data_contract`.

### Tag Taxonomy (MANDATORY)
Every manifest must include at least one tag from this canonical list:
- admin: System administrative (startup, shutdown, maintenance)
- content: Fetches or displays external informational content (quotes, news)
- network: Primary function depends on remote HTTP/API calls
- sensor: Reads local hardware or environmental data
- novelty: Fun or non-critical (jokes, random facts, emoji)
- system: Internal system status or diagnostics
- utility: Simple helper (speed test, tide time, quick lookup)

Multiple tags allowed; choose the most specific pair (e.g. ["content", "network"]).

### Global Timeout Default
Single global default defined at system level (config) or fallback in `AppManifest` (currently 900s). Apps SHOULD override if they naturally complete sooner (<120s typical for content fetch). Avoid excessive durations that hinder responsiveness.

## 4. Entry Point Contract
```
def run(stop_event, api):
    # stop_event: threading.Event signaled when system or timeout requests termination
    # api: AppAPI instance providing screen, hardware, event_bus, logging helpers
    ...
```
Never spawn untracked threads without tying them to `stop_event`. Avoid module-level I/O or network calls at import time.

## 5. Lifecycle & Loop Pattern
Recommended loop:
```
while not stop_event.is_set():
    # perform periodic or reactive work
    stop_event.wait(interval)  # interval 0.25–5.0s
```
Use `stop_event.wait()` rather than busy loops or long `sleep()` calls. For rerun behavior use `timeout_behavior="rerun"` plus optional `timeout_cooldown_seconds`.

## 6. Event System Usage
Subscriptions:
- Subscribe only after initial resource setup.
- Store subscription IDs; unsubscribe in `finally`.
- Avoid broad wildcard topics; use specific names.

Publishing:
- Use meaningful source: `app:<name>` implicitly set by AppAPI.
- Payload objects MUST be JSON-serializable.

Forbidden legacy event names: `switch_change`, `display_update`, `screen_update` (apps should not publish hardware output events directly; use API methods).

## 7. Hardware Parity & Button/LED Coordination
Principle: Button handling only active when its LED is ON.
Pattern:
```
def on_button(event_type, payload):
    btn = payload.get("button")
    if btn not in active_buttons:
        return
    ...
```
Enable LED before processing; disable temporarily for feedback; restore via short timer honoring `stop_event`.

Apps MUST NOT import hardware backend modules (gpio/mock/webui). Interaction only through `api.hardware` and `api.screen`.

## 8. Screen & Display Rules
- 7-seg display is system-controlled; do not call display methods directly (AppAPI set_display is no-op).
- Use `api.screen.display_text(...)` / `clear_screen()` / `display_image()` if available.
- No legacy screen methods (`write_line`, `clear_body`, etc.). Guard test ensures removal.

## 9. Logging & Observability
Use `api.log_info()` / `api.log_error()` or standard logger if contextual. Limit to actionable messages. Avoid high-frequency debug inside loops.

## 10. Timeout Behaviors
- return: Clean stop; system may show startup app automatically.
- rerun: App restarts itself after cooldown; ensure internal state resets.
- none: Long-running; MUST still honor `stop_event`. Use sparingly.

## 11. Clean Shutdown Checklist
In a `try/finally` block:
- Unsubscribe events
- Cancel timers/threads
- Turn off LEDs you enabled
- Clear transient screen state if appropriate
- Avoid raising exceptions in cleanup

## 12. External APIs & Secrets
- Always wrap network calls with timeout and retry (exponential backoff optional).
- Use environment variables or centralized secret loader; never hard-code secrets.
- Publish failure events only if user-visible consequence.

## 13. Performance & Resource Guidelines
- Minimum wait interval: ≥0.05s (never tight microsecond loops).
- Network calls: parallelization via threads discouraged; prefer sequential unless justified.
- Memory: keep assets small (<1MB typical); large data fetches must be streamed or cached.

## 14. Testing Guidelines
- Unit: Use mock hardware backend; assert event publication and LED gating.
- Smoke: Launch each app for short run, ensure no exceptions, verify clean stop.
- Avoid random nondeterministic behavior without seeding.

## 15. Anti-Patterns (Reject During Review)
| Anti-Pattern | Corrective Action |
|--------------|------------------|
| Busy loop without waits | Replace with `stop_event.wait(interval)` |
| Direct GPIO import | Replace with `api.hardware` calls |
| Unconditional `time.sleep(>5)` | Use segmented waits honoring stop_event |
| Missing unsubscribe | Track subscription IDs and remove in `finally` |
| LED left ON after exit | Turn off in cleanup |
| Hard-coded secret/api key | Move to env var / secrets file |
| Network call without timeout | Add `requests.get(..., timeout=5)` or equivalent |
| Using legacy `id`/`title` fields | Replace with `name`/`description` + add `version`/`author` |
| Non-canonical tags | Use only taxonomy tags: admin, content, network, sensor, novelty, system, utility |
| Manifest name mismatch | Ensure `name` field matches directory name exactly |

## 16. Conformance Review Process
1. Inventory & static scan (script).
2. Score on criteria (manifest completeness, lifecycle hygiene, parity, logging discipline).
3. Refactor low-score apps first (admin/system critical, then network, then novelty).
4. CI hook (future) enforces mandatory tags and signature check.

## 17. Manifest Validator
Automated script (`scripts/validate_manifests.py`) enforces:
- JSON validity and parseability
- Required fields: name, description, version, author
- Mandatory tags: at least one canonical taxonomy tag
- Tag validity: all tags must be from canonical list (admin, content, network, sensor, novelty, system, utility)
- Name/directory match: manifest `name` must equal directory name exactly
- timeout_behavior presence and validity (return/rerun/none)
- Deprecated field detection: warns on id/title/assets_required/api_keys/instructions
- Unknown key warnings (except allowed: entry_point, timeout_seconds, timeout_behavior, tags, requires_network, requires_audio, external_apis, required_env, config)

Run validator:
```bash
python scripts/validate_manifests.py
```

Exit code 1 if any critical errors; 0 if warnings only or clean.

## 18. Minimal Starter Template
```json
{
  "name": "starter_template",
  "description": "Baseline app",
  "version": "1.0.0",
  "author": "B.O.S.S. Team",
  "tags": ["utility"],
  "timeout_seconds": 120,
  "timeout_behavior": "return"
}
```
```python
def run(stop_event, api):
    api.log_info("Starter app running")
    sub_id = api.event_bus.subscribe("button_pressed", lambda t,p: api.log_info("Button press"))
    try:
        while not stop_event.is_set():
            stop_event.wait(1.0)
    finally:
        api.event_bus.unsubscribe(sub_id)
        api.screen.clear_screen()
        for c in ["red","yellow","green","blue"]:
            api.hardware.set_led(c, False)
```

## 19. Advanced Example Reference
See `hello_world` app for timers, LED sequencing, inactivity logic, and structured cleanup (do not copy verbatim; prune for minimal cases).

---
This blueprint supersedes informal patterns; all new apps must comply.
