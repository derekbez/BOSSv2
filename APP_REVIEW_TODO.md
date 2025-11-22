# App Review TODO (Mini-App Normalization)

Status Legend: [ ] not started | [~] in progress | [x] completed

## Phase 1: Foundations ✅ COMPLETE
- [x] Add mini-app blueprint document (`.github/instructions/mini_app_blueprint.md`)
- [x] Update `app_authoring.md` with mandatory tags + timeout guidance
- [x] Implement inventory script (`scripts/app_inventory.py`)
- [x] Run inventory & produce `tmp/app_inventory.json`
- [x] Analyze inventory & prioritize refactors (scorecard: JSON validity, schema compliance, tag presence)

## Phase 2: Conformance & Refactor ✅ COMPLETE
- [x] Add mandatory tags to all manifests (classification taxonomy)
- [x] Normalize timeout_seconds values (content/network apps set to 90-180s)
- [x] Migrate legacy `id`/`title` fields to `name`/`description` + add `version`/`author`
- [x] Remove deprecated fields (`assets_required`, `api_keys`, `instructions`)
- [x] Fix non-canonical tags (`weather`→`content`, remove `demo`/`template`)
- [x] Add missing `timeout_behavior` field where absent
- [x] Fix all JSON syntax errors (missing commas)
- [x] Normalize manifest names to match directory names exactly
- [ ] Remove direct hardware imports in any offending apps (audit pending)
- [ ] Ensure run signature matches `run(stop_event, api)` everywhere (audit pending)
- [ ] Add missing cleanup (unsubscribe, LED off, clear_screen) where absent (audit pending)
- [ ] Replace busy loops with `stop_event.wait()` intervals (audit pending)

## Phase 3: Validation & Automation ✅ VALIDATOR COMPLETE
- [x] Draft manifest validator spec (fields, tags, timeout_behavior) — integrated into blueprint
- [x] Implement manifest validator script (`scripts/validate_manifests.py`)
- [x] Validate all 31 manifests: ✅ 31/31 clean (0 errors, 0 warnings)
- [ ] CI integration: fail on missing tags or invalid timeout_behavior (GitHub Actions hook pending)
- [ ] Add smoke test harness (launch each app briefly, confirm clean stop)

## Phase 4: Documentation & Templates
- [ ] Minimal starter template app (`apps/_starter_template`) (optional non-deployed)
- [ ] Refine advanced example (`hello_world`) comments (remove excess verbosity, link to blueprint)
- [ ] Add FAQ section to blueprint (timeouts, tags, screen vs display)

## Future Enhancements (Backlog)
- [ ] App performance metrics (average runtime, event emissions) collector
- [ ] External API health auditing & caching strategy guidance
- [ ] Localization/i18n pattern proposal
- [ ] Telemetry opt-in for app execution stats

## Completed Work Summary (2025-11-22)
**Blueprint Schema:** Formalized `config` as allowed field; documented deprecated fields; updated anti-patterns.
**Manifest Remediation:** Fixed 16 apps (JSON syntax, legacy fields, name normalization, tag corrections).
**Validator Implementation:** Created `scripts/validate_manifests.py` enforcing all blueprint requirements.
**Validation Status:** All 31 manifests pass validation with zero errors/warnings.

## Recommended Workflow
1. Before creating new apps: reference `.github/instructions/mini_app_blueprint.md` + starter template
2. After manifest changes: run `python scripts/validate_manifests.py` to catch issues early
3. Before commits: ensure tests pass (`pytest`) and validator clean
4. Periodic reviews: run inventory script to identify drift or new anti-patterns

## Notes
Option A chosen: Single global default timeout; per-app overrides recommended.
Mandatory tags: admin, content, network, sensor, novelty, system, utility.
Canonical schema: name, description, version, author (required); tags (mandatory); config (optional free-form).
