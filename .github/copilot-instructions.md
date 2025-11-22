# B.O.S.S. Developer & Copilot Instruction Index

This file now serves as a minimal index pointing to focused guidance documents under `.github/instructions/`. Each topic is isolated for clarity and easier maintenance after the architectural flattening (facades: `core`, `hardware`, `config`, `logging`, `ui`).

> IMPORTANT: Mandatory Virtual Environment
> - Always run Python inside a project-local virtual environment (`.venv`).
> - All commands and tooling assume an active venv; running outside a venv is unsupported and leads to inconsistent dependencies.
> - In VS Code, select the `.venv` interpreter (Command Palette → Python: Select Interpreter).

## Core Topics
- Architecture & Principles: `.github/instructions/architecture.md`
- Development Environment & Run Modes: `.github/instructions/development_environment.md`
- Hardware Abstraction & Parity Rules: `.github/instructions/hardware_and_parity.md`
- Mini-App Authoring & Lifecycle: `.github/instructions/app_authoring.md`
- **Mini-App Blueprint (Authoritative Standard):** `.github/instructions/mini_app_blueprint.md`
- Event Bus & Logging Taxonomy: `.github/instructions/event_bus_and_logging.md`
- Configuration & Secrets Handling: `.github/instructions/configuration_and_secrets.md`
- Web UI & Debugging Tools: `.github/instructions/web_ui_and_debugging.md`
- Testing Strategy & Fixtures: `.github/instructions/testing_strategy.md`
- Deployment & Remote Operations: `.github/instructions/deployment_and_remote_ops.md`
- Troubleshooting & Diagnostics: `.github/instructions/troubleshooting.md`

## Quick Start (Venv is mandatory)
1. Create & activate venv, then install deps.
	 - Windows (cmd.exe):
		 ```cmd
		 python -m venv .venv
		 .venv\Scripts\activate
		 python -m pip install --upgrade pip
		 pip install -r requirements/base.txt
		 ```
	 - Windows (PowerShell):
		 ```powershell
		 python -m venv .venv
		 Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
		 .venv\Scripts\Activate.ps1
		 python -m pip install --upgrade pip
		 pip install -r requirements/base.txt
		 ```
	 - macOS/Linux:
		 ```bash
		 python3 -m venv .venv
		 source .venv/bin/activate
		 python -m pip install --upgrade pip
		 pip install -r requirements/base.txt
		 ```
2. Run locally (webui/mock hardware): `python -m boss.main`.
3. For Raspberry Pi deployment: see deployment & remote ops doc.

## HDMI Screen Notes
- Textual terminal UI (no legacy Pillow framebuffer). Logical `screen_width`/`screen_height` in `boss_config.json` control layout.
- Adjust dimensions for readability; they are not pixel mappings.

## LED/Button Parity (Critical UX)
Always gate button events by LED state. Details & code pattern: see hardware parity doc.

## Event Naming Convention
Canonical taxonomy described in event bus doc. Avoid ad-hoc names; follow `input.*`, `output.*`, `system.*` structure.

## When Adding New Functionality
- Update only the relevant instruction file (avoid bloating this index).
- Keep cross-references minimal; prefer a single authoritative location per concept.
- If a new concern doesn’t fit existing files, create an additional markdown in the instructions directory and add it to the list above.

## Legacy Directories Removed
Deprecated layered folders (`presentation`, `application`, `domain`, `infrastructure`) replaced by flattened facade packages. Remove any new references to legacy paths in future contributions.

## Maintenance Checklist
- After structural changes: verify docs still align (run `grep` for legacy names).
- After adding events: update event bus document.
- **After adding/modifying apps:** run `python scripts/validate_manifests.py` to ensure blueprint compliance.
- After changing hardware mapping: reflect in config & hardware parity doc.
- Before commits: ensure tests pass (`pytest`) and manifests validate cleanly.

## Updating This Index
Keep this file short. Link, don’t replicate. Large conceptual edits belong in their dedicated instruction file.

---
This index replaces the previous monolithic guidance. For historical reference see archived docs under `docs/archive/` if needed.
