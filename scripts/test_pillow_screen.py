#!/usr/bin/env python3
"""
Deprecated script: Pillow backend is removed. Use Textual-based terminal UI instead.
"""
import sys

if __name__ == "__main__":
    sys.stderr.write(
        "This script is deprecated. The Pillow framebuffer backend has been removed.\n"
        "Use Textual terminal UI and the web UI/dev tools for screen testing.\n"
    )
    raise SystemExit(1)
