# Migration Plan: Integrating Event Bus into B.O.S.S.

## Overview
This migration plan outlines the steps required to implement the event bus in the B.O.S.S. system, update the API, and refactor mini-apps and core modules for event-driven operation. Follow these steps in order for a smooth transition.

### 1. Design & Implement EventBus Core
- Design the `EventBus` class with thread-safe publish/subscribe, event filtering, and async support.
- Define standard event types and payload schemas.
- Add logging for all published events.

### 2. Integrate EventBus into Core System
- Instantiate a global event bus in the core application (e.g., in `main.py` or a core module).
- Refactor hardware abstraction layers (buttons, switches, etc.) to publish events to the event bus instead of calling callbacks or polling.
- Update core modules (AppManager, Logger, Remote API) to subscribe to relevant events.

### 3. Update the API Object
- Expose the event bus to mini-apps via the API object:
  - Add `api.event_bus.subscribe(event_type, callback, filter=None)`
  - Add `api.event_bus.publish(event_type, payload)`
- Update API documentation to include event bus usage and event type reference.

### 4. Refactor Mini-Apps for Event-Driven Operation
- Refactor existing mini-apps to use event subscriptions instead of polling for hardware state.
- Register event handlers for relevant events (e.g., button presses, switch changes) in each app's entrypoint.
- Remove or minimize polling loops in favor of event-driven logic.
- Update or add tests to use event bus mocks and simulated events.

### 5. Update and Expand Tests
- Add unit and integration tests for the event bus (publish/subscribe, filtering, async delivery).
- Update mini-app and core tests to use the event bus for simulating hardware events.
- Ensure all tests pass in both real and mocked hardware environments.

### 6. Documentation & Examples
- Update all relevant documentation (API docs, developer guides, mini-app templates) to reflect event-driven patterns.
- Provide migration examples and best practices for app developers.

### 7. Review, QA, and Rollout
- Review all changes for backward compatibility and performance.
- Conduct QA with both real and mocked hardware.
- Roll out the event bus integration in a staged manner, monitoring for regressions.

---

# B.O.S.S. Event Bus: Features & User Stories

## Overview
The Event Bus is a core component of B.O.S.S., enabling decoupled, event-driven communication between hardware, core logic, and mini-apps. It allows components to publish and subscribe to events (e.g., button presses, switch changes, app lifecycle events) in a thread-safe, extensible manner.

---

## Features

### 1. Event Publishing & Subscription
- Any component (hardware, core, app) can publish events to the bus.
- Components can subscribe to specific event types or all events.
- Supports multiple subscribers per event type.
- Thread-safe event dispatching.

### 2. Event Types
- Predefined event types include:
  - **Input Events:**
    - `button_press`, `button_release` (color buttons, "go" button)
    - `switch_change` (mux/switches)
  - **Output Events:**
    - `led_state_changed` (red, yellow, green, blue LEDs)
    - `seven_segment_updated` (7-segment display)
    - `screen_updated` (7-inch screen)
  - **App/System Events:**
    - `app_started`, `app_stopped`, `error`, `system_shutdown`, etc.
- Custom event types can be registered by apps or extensions.

### 3. Event Payloads
- Events carry structured payloads (dicts) with relevant data (e.g., button id, led color, value, content, timestamp).
- Payload schema is documented for each event type. Example schemas:
  - `button_press`: `{ "button": "red", "timestamp": ... }`
  - `switch_change`: `{ "value": 42, "previous_value": 41, "timestamp": ... }`
  - `led_state_changed`: `{ "led": "green", "state": "on", "timestamp": ... }`
  - `seven_segment_updated`: `{ "value": 128, "timestamp": ... }`
  - `screen_updated`: `{ "action": "display_text", "content": "Hello!", "timestamp": ... }`

### 4. Synchronous & Asynchronous Handling
- Subscribers can handle events synchronously (blocking) or asynchronously (in a thread or via callback).
- Option to queue events for later processing.

### 5. Event Filtering
- Subscribers can filter events by type, source, or payload content.

### 6. Logging & Debugging
- All events can be logged for debugging and auditing.
- Option to enable/disable event logging per event type.

### 7. Extensibility
- New event types and sources can be added without modifying core code.
- Mini-apps can define and publish custom events.

### 8. Testing & Mocking
- Event bus can be mocked for unit/integration testing.
- Test utilities for simulating events and verifying subscriber responses.

---


Thank you for the guidance! Here’s how I will proceed, applying best practices for simplicity, maintainability, and a user-friendly fallback approach:

---

## Event Bus Implementation Defaults

**Threading Model:**  
- Use standard Python threads for async delivery (not asyncio), as this is easier for most developers to understand and maintain.

**Event Delivery Guarantees:**  
- At-least-once delivery: Each subscriber callback is called for each event, but if a callback fails, it is logged and the system continues.

**Error Handling in Subscribers:**  
- If a subscriber callback raises an exception, log the error (with traceback) and continue delivering to other subscribers. Never let one bad handler break the event bus.

**Unregistering Subscribers:**  
- Support unsubscribe functionality so handlers can be removed if needed (e.g., when a mini-app exits).

**Event Type Registration:**  
- Event schemas are advisory/documentation-only. No runtime schema enforcement, but all core events must match the documented schema.

**Queue Size/Backpressure:**  
- Use a bounded queue for async delivery (e.g., `queue.Queue(maxsize=1000)`). If the queue is full, log a warning and drop the event (never block the main thread or annoy the user).

**Event Ordering:**  
- Best-effort ordering: Events are delivered in the order they are published, but strict ordering is not guaranteed if handlers are slow.

**Performance Requirements:**  
- No hard real-time guarantees. The system is designed for responsiveness but prioritizes robustness and user experience.

---

## Additional Notes

- All logging uses the central logger.
- All hardware and app errors are caught and logged.
- Fallbacks (e.g., if the event bus fails) are silent to the user and do not interrupt normal operation.
- The code will be well-documented and modular, with clear type hints and docstrings.
- Tests will mock the event bus and verify publish/subscribe behavior.

---

