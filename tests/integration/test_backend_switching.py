import json
from pathlib import Path
from unittest.mock import Mock

from boss.application.services.app_manager import AppManager
from boss.application.services.app_runner import AppRunner
from boss.application.services.hardware_service import HardwareManager
from boss.application.events.event_bus import EventBus
from boss.infrastructure.hardware.mock.mock_factory import MockHardwareFactory
from boss.domain.models.config import HardwareConfig, SystemConfig, BossConfig


def make_min_config(tmp_path: Path, backend: str = "rich") -> BossConfig:
    hardware = HardwareConfig(
        switch_data_pin=18,
        switch_select_pins=[22, 23, 25],
        go_button_pin=16,
        button_pins={"red": 5, "yellow": 6, "green": 13, "blue": 19},
        led_pins={"red": 21, "yellow": 20, "green": 26, "blue": 12},
        display_clk_pin=2,
        display_dio_pin=3,
        screen_width=800,
        screen_height=480,
        screen_fullscreen=True,
        screen_backend=backend,
        enable_audio=True,
        audio_volume=0.7,
    )
    system = SystemConfig(
        app_timeout_seconds=10,
        apps_directory="apps",
        log_level="INFO",
        log_file="logs/boss.log",
        log_max_size_mb=10,
        log_backup_count=5,
        event_queue_size=100,
        event_timeout_seconds=1.0,
        webui_enabled=False,
        webui_host="localhost",
        webui_port=8070,
        enable_api=False,
        api_port=5000,
        auto_detect_hardware=True,
        force_hardware_type="mock",
    )
    return BossConfig(hardware=hardware, system=system)


def write_simple_app(tmp_apps: Path, name: str, preferred: str | None):
    app_dir = tmp_apps / name
    app_dir.mkdir(parents=True, exist_ok=True)
    (app_dir / "main.py").write_text(
        """
def run(stop_event, api):
    api.log_info("test app running")
    stop_event.set()
"""
    )
    manifest = {
        "name": name,
        "description": "test",
        "version": "1.0.0",
        "author": "test",
        "entry_point": "main.py",
        "timeout_seconds": 2,
    }
    if preferred:
        manifest["preferred_screen_backend"] = preferred
    (app_dir / "manifest.json").write_text(json.dumps(manifest))
    return app_dir


def test_preferred_backend_applied_and_restored(tmp_path: Path):
    # Arrange environment
    cfg = make_min_config(tmp_path, backend="rich")
    apps_dir = tmp_path / "apps"
    apps_dir.mkdir()
    # map switch 1 to app
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "app_mappings.json").write_text(json.dumps({"app_mappings": {"1": "app_pref_pillow"}}))
    # create app preferring pillow at apps_dir/app_pref_pillow
    write_simple_app(apps_dir, "app_pref_pillow", preferred="pillow")

    # Wire services with mock hardware factory
    event_bus = EventBus(queue_size=100)
    hw_factory = MockHardwareFactory(cfg.hardware)
    hardware = HardwareManager(hw_factory, event_bus)
    app_manager = AppManager(apps_dir, event_bus, hardware_service=hardware)
    app_manager.load_apps()
    runner = AppRunner(event_bus, lambda n, p: Mock())

    # Initialize hardware and set starting backend
    hardware.initialize()
    assert hardware.get_current_screen_backend() == "rich"

    # Act: apply backend for app and simulate run
    app = app_manager.get_app_by_switch_value(1)
    assert app is not None
    prev = app_manager.apply_backend_for_app(app)
    # After applying, backend should be pillow
    assert hardware.get_current_screen_backend() == "pillow"
    # Now restore
    app_manager.restore_backend(prev)
    assert hardware.get_current_screen_backend() == "rich"


def test_config_validation_normalizes_backend(tmp_path: Path):
    from boss.infrastructure.config.config_manager import validate_config
    cfg = make_min_config(tmp_path, backend="RiCh")
    ok = validate_config(cfg)
    assert ok is True
    assert cfg.hardware.screen_backend == "rich"
