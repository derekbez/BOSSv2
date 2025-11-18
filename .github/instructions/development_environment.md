# Development Environment

## Python & Virtual Environment (MANDATORY)
- Require Python 3.11+.
- All development and runtime commands MUST be executed inside a project-local virtual environment (`.venv`). Running outside a venv is unsupported.
- Create local venv (`.venv`) at repo root and activate before installing dependencies:
  - Windows cmd:
    ```cmd
    python -m venv .venv
    .venv\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r requirements/base.txt
    ```
  - PowerShell:
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
- Select interpreter in VSCode: Command Palette → "Python: Select Interpreter" → choose `.venv`.
- Tip: If VS Code reverts the interpreter, re-select `.venv` and reload the window.

## Dependencies
- Base requirements: GPIO (gpiozero/lgpio), TM1637, FastAPI/Uvicorn, Textual/Rich, pytest.
- Install with: `pip install -r requirements/base.txt`.
- Dev tools (if present in `requirements/dev.txt`): install separately when needed.

## Run Modes
| Mode | Flag / Env | Description |
|------|------------|-------------|
| GPIO | `--hardware gpio` or auto-detect | Real Raspberry Pi hardware |
| WebUI | `--hardware webui` or `BOSS_DEV_MODE=1` | Emulated hardware + FastAPI interface |
| Mock | `--hardware mock` or `BOSS_TEST_MODE=1` | Pure mocks for tests/CI |

## Typical Local Run
```bash
python -m boss.main --hardware webui
```
- Opens WebUI on localhost (port from config, default 8070).

## Environment Overrides
| Variable | Effect |
|----------|--------|
| `BOSS_LOG_LEVEL` | Override configured log level |
| `BOSS_CONFIG_PATH` | Point to alternative config JSON |
| `BOSS_TEST_MODE=1` | Force mock hardware + DEBUG logging |
| `BOSS_DEV_MODE=1` | Enable WebUI + DEBUG logging (if not already)|

## Repository Hygiene
- Keep `main` deployable; feature work on branches; merge only with green tests.
- Never commit secrets (`secrets.env` excluded).
- Prefer small, atomic commits with clear messages.

## Performance & Resource Tips
- Avoid large blocking loops in app threads—use events and periodic checks on `stop_event`.
- Textual screen updates should batch content where possible.
- Use logging at INFO by default; DEBUG only when diagnosing.

## Anti-Patterns
- Running outside activated venv leading to missing dependency errors.
- Editing `boss_config.json` and adding comments (file must be strict JSON).
- Direct hardware access in apps (must use `AppAPI`).

## Next Steps
Read `hardware_and_parity.md` then `app_authoring.md`.
