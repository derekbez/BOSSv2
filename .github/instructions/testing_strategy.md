# Testing Strategy

## Test Layers
| Layer | Purpose | Example |
|-------|---------|---------|
| Unit | Validate isolated functions/classes | EventBus publish/subscribe |
| Integration | Exercise composed managers & hardware mocks | SystemManager start/stop |
| Backend Parity | Ensure gpio vs webui vs mock produce same events | LED gating tests |

## Running Tests
```bash
pytest -q
```
Add coverage (optional):
```bash
pytest --cov=boss --cov-report=term
```

## Core Fixtures (Standardized)
Use these fixtures for new tests (defined in `tests/conftest.py`). Legacy ad-hoc mocks may be removed over time.

| Fixture | Provides | Notes |
|---------|----------|-------|
| `event_bus` | Real `EventBus` instance | Auto-stopped after test |
| `boss_config` | `BossConfig` object | Alias of legacy `mock_config` |
| `hardware_factory` | `MockHardwareFactory` | Builds mock devices from config |
| `hardware_manager` | Initialized `HardwareManager` | Devices ready; monitoring not started |
| `apps_dir` | Temp apps directory | Seeded with a sample app via legacy fixture |
| `app_manager` | Loaded `AppManager` | Uses `apps_dir` + config backend |
| `app_api_factory` | Factory returning `AppAPI` | Pass to `AppRunner` |
| `app_runner` | `AppRunner` instance | For launching/stopping apps |
| `system_manager` | Composed `SystemManager` | Mirrors `main.py` composition |

### Helper Modules
| Module | Purpose |
|--------|---------|
| `tests/helpers/app_scaffold.py` | Create mini-apps programmatically (manifest + main) |
| `tests/helpers/runtime.py` | Event-driven wait helpers (no raw sleeps) |

### Creating Apps in Tests
Use `create_app(apps_dir, name, run_body=..., preferred_backend=...)` instead of inline multi-line strings.

## Principles
- Deterministic: prefer event-driven waits (`wait_for_app_started`) over `time.sleep`.
- Fast: aim for < 0.5s per unit test; integration < 2s.
- Isolated: no external services; mock or scaffold everything.
- Explicit Composition: mirror `boss/main.py` through fixtures, not ad-hoc instantiation blocks.

## Mock Hardware Usage
- Use `--hardware mock` or environment `BOSS_TEST_MODE=1` for programmatic test runs.
- Provide explicit initial states (e.g., all LEDs OFF).

## Common Assertions
- Event published once per distinct state change (e.g., switch value).
- App thread terminates when `stop_event` set; use `wait_for_app_finished`.
- LED gating prevents button handler invocation when inactive.
- Backend preference resolves to canonical backend or is ignored if single-backend.

## Skip / Avoid
| Avoid | Reason |
|-------|--------|
| Real GPIO in CI | Unavailable / nondeterministic |
| Arbitrary `time.sleep` | Replaced by event-driven helpers |
| Hidden global state mutations | Causes test order dependency |
| Manual inline app manifests | Use `create_app` helper |

## Adding New Tests
1. Target smallest scope first (unit).
2. Add integration test only if multiple components interplay.
3. Use parametrization for combinatorial hardware cases.

## Failure Diagnosis
- Intermittent event timing: temporarily add DEBUG around publish/subscribe; validate predicates used in waits.
- Thread not stopping: confirm app sets `stop_event`; use `wait_for_app_finished` instead of arbitrary sleep.
- Fixture misconfiguration: print fixture-provided config values to ensure alignment.

## Quality Gates
- All tests green before merge to `main`.
- New feature: at least one unit + (if multi-component) one integration test.
- No new raw sleeps > 0.05s unless justified (document in test).
- Coverage (optional): monitor statement coverage; raise if < target threshold (define once stable).

Next: `deployment_and_remote_ops.md`.
