# Event Bus & Logging

## Event Bus Fundamentals
- Central dispatcher for all system, hardware, and app events.
- Subscribers register callbacks: `sub_id = event_bus.subscribe(event_type, handler)`.
- Publish: `event_bus.publish(event_type, payload, source)`.
- Unsubscribe: `event_bus.unsubscribe(sub_id)`.

## Canonical Event Types
| Category | Examples |
|----------|----------|
| Input | `input.switch.changed`, `input.button.pressed`, `input.button.released` |
| Output | `output.display.updated`, `output.screen.updated`, `output.led.state_changed` |
| Lifecycle | `system.app.started`, `system.app.finished`, `system.shutdown.initiated` |
| Errors | `system.error` (payload includes `code`, `message`) |

Avoid legacy aliases (`switch_change`, `display_update`). Keep taxonomy consistent.

## Naming Conventions
- Use dot-separated lowercase segments.
- Start with domain (input/output/system/app).
- Use past tense or descriptive state for completed events (`updated`, `state_changed`).
- Include payload keys that match event semantics (e.g., display: `{ "value": 42 }`).

## Payload Guidelines
- Keep flat JSON-friendly dictionaries.
- Include `timestamp` only when externally consumed (WebUI or audit); internal handlers can add it.
- Avoid leaking internal object instances—use primitive serializable fields.

## Performance Considerations
- Avoid long-running handlers; offload heavy work to separate threads if necessary.
- High-frequency events (switch changes) should publish only on value change.

## Error Handling
- Catch exceptions inside handlers to prevent subscriber-wide cascade failures.
- Optionally publish `system.error` with context to central logger.

## Logging Standards
- Initialize via `boss.logging.setup_logging(config)`.
- Use module-level logger: `logger = logging.getLogger(__name__)`.
- Levels:
  - DEBUG: Diagnostic, ephemeral.
  - INFO: Lifecycle milestones, state changes.
  - WARNING: Recoverable issues or fallbacks.
  - ERROR: Failed operations requiring attention.
  - CRITICAL: System integrity compromised.

## Structured Logging Tips
- Prefer key-value formatting in messages: `"Switch changed value=%s"`.
- Do not log sensitive secret values.

## Do / Avoid
| Do | Avoid |
|----|-------|
| Unsubscribe on shutdown | Leaving dangling subscribers |
| Publish canonical events | Mixing legacy & new names |
| Keep payload minimal | Passing large blobs / objects |
| Use INFO for state transitions | Spamming DEBUG in production |

## Checklist
- Handlers short & resilient.
- No legacy event names in new code.
- All app subscriptions cleaned on exit.

Next: `configuration_and_secrets.md`.
