# Archived Legacy Mini-App API (2025-08-30)

Preserved from `docs/miniapp_api.md` prior to consolidation. Superseded by `../miniapps_api_events_v2.md`.

Rationale for archival:
* Listed methods (effects, advanced image scaling) not implemented in current simplified backend
* Did not reflect new LED / screen payload field names
* Described synchronous event delivery

---
Original Content:
````markdown
# B.O.S.S. Mini-App API Documentation

## Overview
This document describes the official API provided by the B.O.S.S. (Board Of Switches and Screen) system for use by all mini-apps. All mini-apps must interact with hardware and display exclusively through this API. Direct hardware access is strictly prohibited to ensure portability, testability, and system safety.

---

## API Object
Each mini-app receives an `api` object as an argument to its entrypoint (typically `run(stop_event, api)` or `main(stop_event, api)`). This object exposes all allowed interactions with the B.O.S.S. hardware and system services.

### API Design Principles
- **Abstraction:** All hardware and display access is abstracted.
- **Mockability:** The API is fully mockable for testing and development.
- **Thread-Safe:** All methods are thread-safe.
- **Extensible:** New features are added via the API, not by direct hardware access.

---

## API Reference
... (truncated for brevity) ...
````
