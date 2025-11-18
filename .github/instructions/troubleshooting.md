# Troubleshooting

This guide lists common issues, diagnostic steps, and escalation paths for the B.O.S.S. system after the architecture refactor.

---
## Quick Diagnostic Flow
1. Identify symptom category (startup, hardware, app crash, performance, remote ops).
2. Run targeted commands/scripts below.
3. Check logs (`logs/boss.log*` or systemd journal).
4. Apply corrective action.
5. If unresolved, escalate with captured evidence.

---
## 1. Startup & Service Issues
| Symptom | Cause (Likely) | Fix | Verify |
|---------|----------------|-----|--------|
| Service fails to start | Missing venv / deps | Activate venv & `pip install -r requirements/base.txt` | `systemctl status boss` OK |
| Import errors for old packages | Legacy path remnants | Clear `__pycache__` & ensure flattened module imports | Run `python -m boss.main` locally |
| Logger module conflict | Shadowing stdlib `logging` | Ensure `boss/logging` uses package import not root name conflicts | Check first lines of runtime log |
| Config validation failure | Invalid JSON / missing keys | Open `boss/config/boss_config.json`, fix structure | Startup log shows config summary |

Commands:
```bash
sudo journalctl -u boss -n 80 --no-pager
sudo systemctl restart boss
python scripts/clean_pycache.py
```

---
## 2. Hardware Access Problems
| Symptom | Cause | Fix | Verify |
|---------|-------|-----|--------|
| GPIO errors (permission) | Missing groups | Add user to `gpio`, `video`, `audio` groups | `groups` lists needed groups |
| TM1637 display not updating | Wiring or pin mismatch | Confirm `display_clk_pin`, `display_dio_pin` in config | Display shows test pattern |
| Buttons ignored though pressed | LED gating active | Ensure LED is ON for expected button | Turn LED on, re-test |
| Switch readings all zero | Mux miswired or select pins wrong | Verify `switch_select_pins` ordering | Switch state log events vary |

Commands:
```bash
python scripts/test_tm1637_display.py
python scripts/test_led_blink.py
python scripts/test_new_architecture.py  # sanity tests
```

---
## 3. Web UI / Development Mode
| Symptom | Cause | Fix | Verify |
|---------|-------|-----|--------|
| Web UI not loading | Port conflict / app not started | Check startup log and port; ensure dev mode flag | Access UI in browser |
| Buttons clickable when LEDs off | Parity rule bypassed in custom code | Review app for direct button handling | LED gating restored |
| No websocket events | Event bus subscription missing | Confirm event publication & subscription names | Browser dev tools show events |

Commands:
```bash
python scripts/check_webui.py
```

---
## 4. Mini-App Execution
| Symptom | Cause | Fix | Verify |
|---------|-------|-----|--------|
| App never starts | Mapping missing or wrong | Update `config/app_mappings.json` | Startup log lists loaded app |
| App hangs on exit | Missing `stop_event` handling | Add periodic checks in app loop | App exits cleanly on timeout |
| App crashes with KeyError | Manifest missing fields | Validate `manifest.json` against template | App runs without exceptions |
| Random LED states leftover | Missing cleanup | Ensure `finally` block turns off LEDs | LEDs off after app end |

Commands:
```bash
python -m boss.main  # run locally
```

---
## 5. Performance & Stability
| Symptom | Cause | Fix | Verify |
|---------|-------|-----|--------|
| High CPU usage | Tight loop without sleep | Add small delay or event-driven refactor | Top shows stable lower CPU |
| Memory growth | Accumulating event subscriptions | Unsubscribe in `finally` | Subscription count stable |
| Slow startup | Excessive hardware probing | Cache detection or reduce retries | Startup time reduced |

---
## 6. Configuration & Secrets
| Symptom | Cause | Fix | Verify |
|---------|-------|-----|--------|
| Env var overrides ignored | Not exported / wrong name | Use correct prefix (`BOSS_`) | Logs reflect new value |
| Secrets not loaded | Missing `.env` file or path | Copy `secrets.sample.env` to `secrets.env` | Secret-dependent feature works |

---
## 7. Remote Management
| Symptom | Cause | Fix | Verify |
|---------|-------|-----|--------|
| Remote deploy fails | SSH key not installed | Run SSH setup command | Passwordless login works |
| Cannot view logs remotely | Network/host mismatch | Update host config & retry | Logs stream in console |
| Service restarts repeatedly | Crash loop | Inspect last 200 journal lines | Root cause fixed, stable |

Commands:
```bash
python scripts/boss_remote_manager.py status
python scripts/boss_remote_manager.py logs
python scripts/boss_remote_manager.py test
```

---
## 8. Event Bus Issues
| Symptom | Cause | Fix | Verify |
|---------|-------|-----|--------|
| Missing expected events | Naming mismatch | Align with taxonomy in event bus docs | Events appear in log |
| Duplicate handlers firing | Subscription not removed | Unsubscribe on teardown | Single handler invocation |
| Log flood | Overly verbose level | Adjust `log_level` or throttle publishing | Log volume reduced |

---
## 9. When to Escalate
Escalate (open an issue) when:
- Repeated crash loops with no clear log cause.
- Hardware anomaly persists after wiring & config checks.
- Data corruption in config or mappings.
- Security concern (unexpected network access / privilege errors).

Include in issue:
- Steps to reproduce
- Relevant excerpt (≤200 lines) from journal or `logs/boss.log`
- Hardware state summary (pins, groups)
- App name and manifest (if app-specific)

---
## 10. Clean Recovery Steps
1. Stop service: `sudo systemctl stop boss`
2. Backup config: copy `boss/config/*.json` elsewhere.
3. Clear caches: `python scripts/clean_pycache.py`
4. Reinstall deps (if corrupted): `pip install -r requirements/base.txt`
5. Restart: `sudo systemctl start boss`

---
## 11. Reference Scripts
- `scripts/test_new_architecture.py`: Core structural sanity.
- `scripts/clean_pycache.py`: Remove stale bytecode.
- `scripts/boss_remote_manager.py`: Remote ops & diagnostics.
- `scripts/test_led_blink.py`: LED hardware quick test.
- `scripts/test_tm1637_display.py`: Display validation.

---
## 12. Common Pitfalls & Prevention
| Pitfall | Prevention |
|---------|-----------|
| Direct hardware access in app | Use API abstraction only |
| Forgetting LED gating | Follow hardware parity guide |
| Hard-coded absolute paths | Use relative paths within `boss` package |
| Event name drift | Centralize in constants or taxonomy doc |
| Missing cleanup of subscriptions | Always track IDs and unsubscribe |

---
## 13. Version Mismatch
If versions conflict:
1. Check `requirements/base.txt` pinned versions.
2. Run `pip freeze` and compare.
3. Align by reinstalling requirements.

Command:
```bash
pip install --force-reinstall -r requirements/base.txt
```

---
## 14. Log Interpretation Tips
- Startup summary: Look for hardware detection lines and config echo.
- Event spam: Filter by level or temporarily disable a noisy publisher.
- Crash point: Identify last successful log before traceback.

---
## 15. Final Checklist Before Escalating
- [ ] Reproduced issue twice
- [ ] Captured minimal log slice
- [ ] Confirmed config validity
- [ ] Verified hardware groups & pins
- [ ] Isolated to specific app or system

---
Prepared for modular documentation architecture; keep this updated as new failure modes emerge.
