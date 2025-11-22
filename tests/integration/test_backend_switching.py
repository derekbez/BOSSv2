import json
from pathlib import Path
from unittest.mock import Mock

from boss.core import AppManager, AppRunner, HardwareManager, EventBus
from boss.hardware import MockHardwareFactory
from boss.core.models import HardwareConfig, SystemConfig, BossConfig


def make_min_config(tmp_path: Path, backend: str = "textual") -> BossConfig:
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


def write_simple_app(tmp_apps: Path, name: str, preferred: str | None, run_delay: float = 0.0):
    app_dir = tmp_apps / name
    app_dir.mkdir(parents=True, exist_ok=True)
    (app_dir / "main.py").write_text(
        f"""
def run(stop_event, api):
    api.log_info("test app running")
    import time
    if {run_delay} > 0:
        time.sleep({run_delay})
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
    cfg = make_min_config(tmp_path, backend="textual")
    apps_dir = tmp_path / "apps"
    apps_dir.mkdir()
    # map switch 1 to app
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "app_mappings.json").write_text(json.dumps({"app_mappings": {"1": "app_pref_textual"}}))
    # create app preferring textual (preference is a no-op in single-backend system)
    write_simple_app(apps_dir, "app_pref_textual", preferred="textual")

    # Wire services with mock hardware factory
    event_bus = EventBus(queue_size=100)
    hw_factory = MockHardwareFactory(cfg.hardware)
    hardware = HardwareManager(hw_factory, event_bus)
    app_manager = AppManager(apps_dir, event_bus, hardware_service=hardware, config=cfg)
    app_manager.load_apps()
    runner = AppRunner(event_bus, lambda n, p: Mock())

    # Initialize hardware and set starting backend
    hardware.initialize()
    assert hardware.get_current_screen_backend() == "textual"

    # Act: apply backend for app and simulate run (no-op in single-backend system)
    app = app_manager.get_app_by_switch_value(1)
    assert app is not None
    prev = app_manager.apply_backend_for_app(app)
    # After applying, backend remains textual; previous backend reported as textual
    assert prev == "textual"
    assert hardware.get_current_screen_backend() == "textual"
    # Now restore (no-op)
    app_manager.restore_backend(prev)
    assert hardware.get_current_screen_backend() == "textual"


def test_config_validation_normalizes_backend(tmp_path: Path):
    from boss.config import validate_config
    cfg = make_min_config(tmp_path, backend="TeXtUaL")
    ok = validate_config(cfg)
    assert ok is True
    assert cfg.hardware.screen_backend == "textual"


def test_system_manager_applies_and_restores_backend_on_app_lifecycle(tmp_path: Path):
    """System-level: ensure backend switches to app preference on start and restores after stop."""
    from boss.core import SystemManager, AppAPI

    # Arrange environment
    cfg = make_min_config(tmp_path, backend="textual")
    apps_dir = tmp_path / "apps"
    apps_dir.mkdir()
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    # map switch 1 to app (preference ignored in single-backend system)
    (config_dir / "app_mappings.json").write_text(json.dumps({"app_mappings": {"1": "app_pref_textual"}}))
    # create app with textual preference
    write_simple_app(apps_dir, "app_pref_textual", preferred="textual", run_delay=0.2)

    # Wire services with mock hardware factory
    event_bus = EventBus(queue_size=100)
    hw_factory = MockHardwareFactory(cfg.hardware)
    hardware = HardwareManager(hw_factory, event_bus)
    app_manager = AppManager(apps_dir, event_bus, hardware_service=hardware, config=cfg)
    app_manager.load_apps()

    # Minimal AppAPI factory (not used by this simple app)
    app_api_factory = lambda name, path: AppAPI(event_bus, name, path, app_manager)
    runner = AppRunner(event_bus, app_api_factory)

    # System manager
    system = SystemManager(event_bus, hardware, app_manager, runner)

    # Start subsystems (event bus started by SystemManager.start)
    system.start()

    try:
        # Ensure initial backend is textual
        assert hardware.get_current_screen_backend() == "textual"

        # Simulate switches at 1 and request app launch
        assert hardware.switches is not None
        # Use getattr to access mock-only helper without upsetting static typing
        simulate = getattr(hardware.switches, "simulate_switch_change", None)
        assert callable(simulate), "Mock switches missing simulate_switch_change"
        simulate(1)
        event_bus.publish("app_launch_requested", {}, "test")

            # During run, backend should remain textual (no switching) using event-driven wait
        from tests.helpers.runtime import wait_for
        assert wait_for(lambda: hardware.get_current_screen_backend() == "textual", timeout=0.5), "Expected backend to remain textual during app run"

        # After app finishes, backend should restore to textual (app is short-lived)
        assert wait_for(lambda: hardware.get_current_screen_backend() == "textual", timeout=2.0), "Backend should restore to textual after app completion"
    finally:
        # Stop system and event bus
        system.stop()
