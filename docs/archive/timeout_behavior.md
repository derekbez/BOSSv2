# App timeout behavior

This document describes the per-app timeout behavior supported by B.O.S.S.

Fields
- `timeout_seconds` (int): how long the runner waits before triggering a timeout.
- `timeout_behavior` (string): what to do when a timeout occurs. Allowed values:
  - `return` - stop the app and return to startup screen (default).
  - `rerun`  - stop and immediately relaunch the same app after a short cooldown.
  - `none`   - ignore timeout; app will not be stopped by the runner.
- `timeout_cooldown_seconds` (optional int): when `rerun` is used, wait this many seconds before relaunch.

Tag-based defaults
- If a manifest does not specify `timeout_behavior`, the runner uses tag-based inference:
  - apps with tags `weather` or `network` default to `rerun`.
  - otherwise default to `return`.

Implementation notes
- The runner publishes `app_stopped` with `reason` set to `timeout` when a timeout occurs.
- For `return` behavior the runner publishes an additional `return_to_startup` event to allow the system manager to show the startup UI.
- `rerun` reuses the same `App` object to relaunch the app. If the relaunch fails, the error is logged.

Testing
- Unit tests cover the three behaviors and verify app lifecycle transitions and published events.

Examples
- `list_all_apps` should set `"timeout_behavior": "none"` in its manifest.
- `current_weather` should set `"timeout_behavior": "rerun"` in its manifest.
