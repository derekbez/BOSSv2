"""Sync secrets between local dev machine and Raspberry Pi.

Usage (Windows CMD examples):
  python scripts/sync_secrets.py push --host pi
  python scripts/sync_secrets.py pull --host pi
  python scripts/sync_secrets.py verify --host pi

Assumptions:
* SSH key auth already set up.
* Remote secrets file: /etc/boss/secrets.env
* Local secrets file:  secrets/secrets.env

The script NEVER prints secret values; it only reports hashes & existence.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
from pathlib import Path
import sys

LOCAL_FILE = Path(__file__).resolve().parent.parent / "secrets" / "secrets.env"
REMOTE_FILE = "/etc/boss/secrets.env"
REMOTE_DIR = "/etc/boss"
REMOTE_STAGE = "/tmp/boss_secrets.env"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def push(host: str) -> None:
        """Upload secrets to remote host, creating directory if first time.

        Strategy:
            1. Ensure /etc/boss exists with secure perms (sudo mkdir -p ...).
            2. Copy locally to a world-writable neutral staging path /tmp (no sudo scp needed).
            3. Move into place with sudo, set ownership root:root and chmod 600.
        This avoids scp failing when directory doesn't exist yet.
        """
        if not LOCAL_FILE.exists():
                print("Local secrets file missing:", LOCAL_FILE)
                sys.exit(1)
        print(f"Preparing remote directory on {host}...")
        run(["ssh", host, f"sudo mkdir -p {REMOTE_DIR} && sudo chown root:root {REMOTE_DIR} && sudo chmod 750 {REMOTE_DIR}"])
        print(f"Staging upload to {host}:{REMOTE_STAGE}")
        run(["scp", str(LOCAL_FILE), f"{host}:{REMOTE_STAGE}"])
        print("Installing secrets file with secure permissions...")
        run(["ssh", host, f"sudo mv {REMOTE_STAGE} {REMOTE_FILE} && sudo chown root:root {REMOTE_FILE} && sudo chmod 600 {REMOTE_FILE}"])
        remote_hash = run(["ssh", host, f"sudo sha256sum {REMOTE_FILE} | cut -d' ' -f1"]).stdout.strip()
        print("Remote hash:", remote_hash)
        print("Local  hash:", sha256(LOCAL_FILE))
        print("Push complete.")


def pull(host: str) -> None:
    print(f"Pulling {host}:{REMOTE_FILE} -> {LOCAL_FILE}")
    LOCAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Use sudo cat to bypass restrictive perms
    try:
        result = run(["ssh", host, f"sudo cat {REMOTE_FILE}"])
    except subprocess.CalledProcessError as e:
        print("Remote file missing or unreadable.")
        raise
    LOCAL_FILE.write_text(result.stdout, encoding="utf-8")
    print("Local hash:", sha256(LOCAL_FILE))
    print("Pull complete.")


def verify(host: str) -> None:
    if not LOCAL_FILE.exists():
        print("Local secrets file missing; cannot verify.")
        sys.exit(1)
    local = sha256(LOCAL_FILE)
    remote = run(["ssh", host, f"sudo sha256sum {REMOTE_FILE} 2>/dev/null | cut -d' ' -f1"]).stdout.strip()
    if not remote:
        print("Remote file missing.")
        sys.exit(2)
    status = "MATCH" if local == remote else "DIFF"
    print(f"Local:  {local}\nRemote: {remote}\nStatus: {status}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync BOSS secrets between local and Pi")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("push", "pull", "verify"):
        p = sub.add_parser(name)
        p.add_argument("--host", required=True, help="SSH host (e.g. pi or user@host)")
    args = parser.parse_args()
    try:
        if args.cmd == "push":
            push(args.host)
        elif args.cmd == "pull":
            pull(args.host)
        else:
            verify(args.host)
    except subprocess.CalledProcessError as e:
        print("Command failed:", " ".join(e.cmd))
        print(e.stderr)
        sys.exit(e.returncode)


if __name__ == "__main__":  # pragma: no cover
    main()
