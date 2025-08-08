import json
from pathlib import Path

from boss.domain.models.app import AppManifest, App


def test_manifest_includes_preferred_backend(tmp_path: Path):
    manifest_data = {
        "name": "demo",
        "description": "test",
        "version": "1.0.0",
        "author": "me",
        "preferred_screen_backend": "rich"
    }
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(manifest_data))
    m = AppManifest.from_file(p)
    assert m.preferred_screen_backend == "rich"
    d = m.to_dict()
    assert d.get("preferred_screen_backend") == "rich"


def test_app_should_use_rich_backend_logic(tmp_path: Path):
    # Prepare entry point files
    (tmp_path / "main.py").write_text("# entry")

    # Explicit rich
    m = AppManifest(name="a", description="b", version="1", author="x", preferred_screen_backend="rich")
    app = App(switch_value=1, manifest=m, app_path=tmp_path)
    assert app.should_use_rich_backend("pillow") is True

    # Explicit pillow
    m2 = AppManifest(name="a2", description="b", version="1", author="x", preferred_screen_backend="pillow")
    app2 = App(switch_value=2, manifest=m2, app_path=tmp_path)
    assert app2.should_use_rich_backend("rich") is False

    # Auto follows system default
    m3 = AppManifest(name="a3", description="b", version="1", author="x", preferred_screen_backend="auto")
    app3 = App(switch_value=3, manifest=m3, app_path=tmp_path)
    assert app3.should_use_rich_backend("rich") is True
    assert app3.should_use_rich_backend("pillow") is False
