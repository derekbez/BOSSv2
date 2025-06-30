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

## User Stories

### US-EB-001: Publish/Subscribe to Hardware Events
As a developer, I want to subscribe to button press, switch change, LED state, display, and screen update events so that my mini-app or core logic can react to user input and system output in real time.
- **Acceptance Criteria:**
  - Mini-apps can register callbacks for `button_press`, `button_release`, `switch_change`, `led_state_changed`, `seven_segment_updated`, and `screen_updated` events.
  - When a button is pressed, a switch changes, an LED changes state, the 7-segment display updates, or the screen is updated, the event bus notifies all subscribers with the correct payload.

### US-EB-002: Decoupled App Lifecycle Management
As a system architect, I want the core system to publish `app_started` and `app_stopped` events so that other components (e.g., logger, remote API) can react to app lifecycle changes without tight coupling.
- **Acceptance Criteria:**
  - The event bus publishes `app_started` and `app_stopped` events with app name and timestamp.
  - Subscribers (e.g., logger) receive and process these events.

### US-EB-003: Custom Event Types for Mini-Apps
As a mini-app developer, I want to define and publish custom event types so that my app can communicate complex state changes or results to the system or other apps.
- **Acceptance Criteria:**
  - Mini-apps can register new event types and publish events with custom payloads.
  - Other components can subscribe to these custom events.

### US-EB-004: Event Filtering and Selective Subscription
As a developer, I want to subscribe only to events matching certain criteria (e.g., only `button_press` for the red button, or only `led_state_changed` for the green LED) so that my code is efficient and focused.
- **Acceptance Criteria:**
  - Subscribers can specify filters (event type, source, payload fields) when subscribing.
  - Only matching events are delivered to the subscriber.

### US-EB-005: Event Logging and Auditing
As a system administrator, I want all events (input and output) to be logged with timestamps and payloads so that I can audit system behavior and debug issues.
- **Acceptance Criteria:**
  - The event bus logs all events to the central logger.
  - Log output includes event type, source, timestamp, and payload.
  - Logging can be enabled/disabled per event type.

### US-EB-006: Asynchronous Event Handling
As a developer, I want to handle events asynchronously so that my app remains responsive even when processing complex events.
- **Acceptance Criteria:**
  - The event bus supports asynchronous (threaded or callback) event delivery.
  - Subscribers can choose between synchronous and asynchronous handling.

### US-EB-007: Testability and Mocking
As a developer, I want to mock the event bus in tests so that I can simulate hardware and output events and verify my app's response without real hardware.
- **Acceptance Criteria:**
  - The event bus can be replaced with a mock in unit/integration tests.
  - Test utilities exist for publishing simulated events and capturing subscriber responses.

### US-EB-008: Extensible Event System
As a system maintainer, I want to add new event types and sources (including new hardware or output devices) without modifying the core event bus code so that the system can evolve over time.
- **Acceptance Criteria:**
  - New event types and sources can be registered at runtime.
  - The event bus API is stable and documented.

### US-EB-009: System Shutdown and Error Events
As a system administrator, I want the event bus to publish `system_shutdown` and `error` events so that all components can respond appropriately to critical system changes.
- **Acceptance Criteria:**
  - The event bus publishes `system_shutdown` and `error` events with relevant payloads.
  - Subscribers can perform cleanup or alerting in response.

---

## Future Enhancements
- Distributed event bus for multi-device scenarios.
- Event replay and persistence for debugging.
- WebSocket or remote event subscription for remote management tools.
