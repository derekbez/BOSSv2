# Archived Legacy Event Schema (2025-08-30)

Superseded by consolidated `../miniapps_api_events_v2.md`.

Major divergences from current authoritative version:
1. LED payload keys: `led`/`state` vs new `color`/`is_on`
2. Screen payload key `data` vs new `content`
3. Claimed synchronous delivery; implementation now uses queue + worker thread
4. Included app control of 7‑seg display (removed from app scope)
5. Added new shutdown reasons (reboot, poweroff, exit_to_os) since legacy draft

---
Original excerpt:
````markdown
# B.O.S.S. Event Schema - New Architecture
... (legacy content truncated) ...
````
