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

## Fixtures (Suggested)
- `event_bus()` – fresh bus instance.
- `hardware_factory(mock)` – mock devices.
- `app_api(sample_app)` – controlled AppAPI for targeted behavior.

## Principles
- Deterministic: avoid real network timing unless explicitly tested.
- Fast: each unit test < 0.5s ideally.
- Isolated: no reliance on external secrets unless mocked.

## Mock Hardware Usage
- Use `--hardware mock` or environment `BOSS_TEST_MODE=1` for programmatic test runs.
- Provide explicit initial states (e.g., all LEDs OFF).

## Common Assertions
- Event published once per state change.
- App thread terminates when `stop_event` set.
- LED gating prevents button handler invocation when inactive.

## Skip / Avoid
| Avoid | Reason |
|-------|--------|
| Real GPIO in CI | Unstable & unavailable |
| Random sleeps > necessary | Slows suite |
| Hidden global state mutations | Test pollution |

## Adding New Tests
1. Target smallest scope first (unit).
2. Add integration test only if multiple components interplay.
3. Use parametrization for combinatorial hardware cases.

## Failure Diagnosis
- Intermittent event timing: add temporary DEBUG logging around publish/subscribe path.
- Thread not stopping: ensure `stop_event.wait()` pattern over raw `time.sleep()`.

## Quality Gates
- All tests green before merge to `main`.
- New feature must include at least one test covering success path & edge case.

Next: `deployment_and_remote_ops.md`.
