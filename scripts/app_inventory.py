"""App Inventory & Static Profile Script

Generates a JSON (and optional CSV) summary of all mini-apps under `boss/apps`.
Captures manifest metadata and basic static signals from `main.py` for review.

Usage (from repository root after activating venv):
  python scripts/app_inventory.py --json tmp/app_inventory.json
  python scripts/app_inventory.py --csv tmp/app_inventory.csv

Fields Collected:
- name, path, manifest_presence, manifest_valid
- tags (list), timeout_seconds, timeout_behavior
- requires_network, requires_audio
- external_apis count, required_env count
- has_run_signature (run(stop_event, api))
- imports_hardware_directly (boolean)
- uses_led_api, uses_screen_api, uses_event_subscribe, uses_event_unsubscribe
- potential_busy_loop (heuristic detection of while True without stop_event)

Exit code 0 on success; >0 if manifest parsing failures encountered.
"""

from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any

RE_RUN_SIGNATURE = re.compile(r"def\s+run\s*\(\s*stop_event\s*,\s*api\s*\)")
RE_EVENT_SUB = re.compile(r"\.event_bus\.subscribe\(")
RE_EVENT_UNSUB = re.compile(r"\.event_bus\.unsubscribe\(")
RE_LED_API = re.compile(r"\.hardware\.set_led\(")
RE_SCREEN_API = re.compile(r"\.screen\.(display_text|display_image|clear_screen)\(")
RE_BUSY_LOOP = re.compile(r"while\s+True:\s*$")
RE_DIRECT_HARDWARE_IMPORT = re.compile(r"from\s+boss\.hardware|import\s+boss\.hardware")

MANDATORY_TAGS = {"admin","content","network","sensor","novelty","system","utility"}

def parse_manifest(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {"data": data, "error": None}
    except Exception as e:
        return {"data": None, "error": str(e)}

def profile_app(app_dir: Path) -> Dict[str, Any]:
    manifest_path = app_dir / "manifest.json"
    main_path = app_dir / "main.py"
    result: Dict[str, Any] = {
        "name": app_dir.name,
        "path": str(app_dir),
        "manifest_present": manifest_path.exists(),
        "manifest_valid": False,
        "manifest_error": None,
        "tags": [],
        "missing_tags": False,
        "timeout_seconds": None,
        "timeout_behavior": None,
        "requires_network": False,
        "requires_audio": False,
        "external_apis_count": 0,
        "required_env_count": 0,
        "has_run_signature": False,
        "imports_hardware_directly": False,
        "uses_led_api": False,
        "uses_screen_api": False,
        "uses_event_subscribe": False,
        "uses_event_unsubscribe": False,
        "potential_busy_loop": False,
    }

    if manifest_path.exists():
        manifest_info = parse_manifest(manifest_path)
        if manifest_info["data"]:
            m = manifest_info["data"]
            result["manifest_valid"] = True
            result["tags"] = m.get("tags", []) or []
            result["missing_tags"] = not any(t in MANDATORY_TAGS for t in result["tags"])
            result["timeout_seconds"] = m.get("timeout_seconds")
            result["timeout_behavior"] = m.get("timeout_behavior")
            result["requires_network"] = bool(m.get("requires_network"))
            result["requires_audio"] = bool(m.get("requires_audio"))
            result["external_apis_count"] = len(m.get("external_apis", []) or [])
            result["required_env_count"] = len(m.get("required_env", []) or [])
        else:
            result["manifest_error"] = manifest_info["error"]
    else:
        result["manifest_error"] = "missing manifest.json"

    if main_path.exists():
        try:
            text = main_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            text = ""
        result["has_run_signature"] = bool(RE_RUN_SIGNATURE.search(text))
        result["imports_hardware_directly"] = bool(RE_DIRECT_HARDWARE_IMPORT.search(text))
        result["uses_led_api"] = bool(RE_LED_API.search(text))
        result["uses_screen_api"] = bool(RE_SCREEN_API.search(text))
        result["uses_event_subscribe"] = bool(RE_EVENT_SUB.search(text))
        result["uses_event_unsubscribe"] = bool(RE_EVENT_UNSUB.search(text))
        # Busy loop heuristic: presence of `while True:` without stop_event usage nearby.
        if RE_BUSY_LOOP.search(text) and "stop_event" not in text.split("while True:")[1][:200]:
            result["potential_busy_loop"] = True
    return result

def collect_apps(root: Path) -> Dict[str, Any]:
    apps_root = root / "boss" / "apps"
    entries = [d for d in apps_root.iterdir() if d.is_dir() and not d.name.startswith("_")]
    return {"apps": [profile_app(d) for d in sorted(entries, key=lambda p: p.name)]}

def write_csv(data: Dict[str, Any], path: Path) -> None:
    import csv
    apps = data["apps"]
    if not apps:
        return
    fieldnames = list(apps[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in apps:
            w.writerow(row)

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Inventory BOSS mini-apps")
    parser.add_argument("--json", type=Path, help="Write JSON summary to file")
    parser.add_argument("--csv", type=Path, help="Write CSV summary to file")
    parser.add_argument("--print", action="store_true", help="Print JSON to stdout")
    args = parser.parse_args(argv)

    repo_root = Path(__file__).parent.parent
    data = collect_apps(repo_root)

    # Error if any manifest invalid
    invalid = [a for a in data["apps"] if not a["manifest_valid"]]
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(data, indent=2), encoding="utf-8")
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        write_csv(data, args.csv)
    if args.print or (not args.json and not args.csv):
        print(json.dumps(data, indent=2))
    if invalid:
        print(f"Found {len(invalid)} apps with invalid or missing manifests", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
