"""
Deprecated script: Pillow framebuffer testing is no longer supported.
Use the Textual terminal UI stack and dev tools instead.
"""
import sys

if __name__ == "__main__":
    sys.stderr.write(
        "This script is deprecated. The Pillow framebuffer backend has been removed.\n"
        "Refer to docs and scripts/test_rich_backend.py for display testing approaches.\n"
    )
    raise SystemExit(1)
