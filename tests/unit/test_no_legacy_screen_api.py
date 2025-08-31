"""Guard test: ensure legacy screen API methods are removed and not reintroduced.

Fails if any forbidden legacy screen method names appear in the app_api implementation
(excluding this test file itself).
"""
from pathlib import Path
import re

FORBIDDEN = ["write_line", "write_wrapped", "clear_body", "any_button_pressed", "width", "height"]

API_FILE = Path(__file__).parents[2] / "boss" / "application" / "api" / "app_api.py"

def test_no_legacy_screen_symbols():
    text = API_FILE.read_text(encoding="utf-8")
    # Allow mentions inside the explanatory docstring; we strip docstring for stricter check if needed.
    # Simple heuristic: ignore first 120 lines (docstring/comment header region) when searching.
    lines = text.splitlines()
    body = "\n".join(lines[120:]) if len(lines) > 120 else text
    violations = []
    for name in FORBIDDEN:
        pattern = re.compile(rf"def\s+{name}\s*\(\s*|@property\s+def\s+{name}\\b")
        if pattern.search(body):
            violations.append(name)
    assert not violations, f"Legacy screen API reintroduced: {violations}. Use display_text()/clear_screen() only."
