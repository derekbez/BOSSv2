# Deployment & Remote Operations

## Target Environment
- Raspberry Pi (64-bit Lite OS, no desktop).
- Required groups: `gpio`, `video`, `audio` for hardware access.

## Systemd Service Setup
```bash
cd ~/boss
./scripts/setup_systemd_service.sh
sudo systemctl start boss
sudo systemctl enable boss
```

## Service Management
```bash
sudo systemctl status boss
sudo systemctl restart boss
sudo journalctl -u boss -f
```

## Remote Manager (From Dev Machine)
```bash
python scripts/boss_remote_manager.py start
python scripts/boss_remote_manager.py status
python scripts/boss_remote_manager.py logs
python scripts/boss_remote_manager.py test
python scripts/boss_remote_manager.py ssh-setup
```

## Deployment Workflow
1. Develop & test locally (mock/webui).
2. Commit & push feature branch.
3. Merge to `main` (tests green).
4. Pull on Pi host or use remote manager deploy action.
5. Restart service & watch logs.

## Upgrade Strategy
- Prefer atomic deploy: update code → restart service.
- Keep previous tag/commit reference for rollback.
- Tag releases with semantic versioning (`vX.Y.Z`).

## Rollback
```bash
git checkout <previous_tag>
sudo systemctl restart boss
```

## Logs & Observability
- Primary log file path from config (`logs/boss.log`).
- Use `journalctl -u boss` for service wrapper logs.

## Security Considerations
- Use SSH keys (no password auth).
- Never store secrets in git; load from environment or `secrets.env` on device with proper permissions.
- Limit exposed network interfaces (WebUI dev only on localhost by default).

## Resource Constraints
- Monitor CPU/RAM usage for runaway apps; enforce timeouts.
- Avoid infinite loops without sleep or event waits.

## Checklist for Production Deploy
- [ ] Config matches hardware pins.
- [ ] Log level set appropriately (INFO).
- [ ] No DEBUG spam in logs after warm-up.
- [ ] Service restarts cleanly with no lingering threads.

Next: `troubleshooting.md`.
