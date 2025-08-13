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


def test_system_manager_applies_and_restores_backend_on_app_lifecycle(tmp_path: Path):
    """System-level: ensure backend switches to app preference on start and restores after stop."""
    from boss.application.services.system_service import SystemManager
    from boss.application.api.app_api import AppAPI

    # Arrange environment
    cfg = make_min_config(tmp_path, backend="rich")
    apps_dir = tmp_path / "apps"
    apps_dir.mkdir()
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    # map switch 1 to app
    (config_dir / "app_mappings.json").write_text(json.dumps({"app_mappings": {"1": "app_pref_pillow"}}))
    # create app preferring pillow, with a small delay to sample during run
    write_simple_app(apps_dir, "app_pref_pillow", preferred="pillow", run_delay=0.2)

    # Wire services with mock hardware factory
    event_bus = EventBus(queue_size=100)
    hw_factory = MockHardwareFactory(cfg.hardware)
    hardware = HardwareManager(hw_factory, event_bus)
    app_manager = AppManager(apps_dir, event_bus, hardware_service=hardware)
    app_manager.load_apps()

    # Minimal AppAPI factory (not used by this simple app)
    app_api_factory = lambda name, path: AppAPI(event_bus, name, path)
    runner = AppRunner(event_bus, app_api_factory)

    # System manager
    system = SystemManager(event_bus, hardware, app_manager, runner)

    # Start subsystems (event bus started by SystemManager.start)
    system.start()

    try:
        # Ensure initial backend is rich
        assert hardware.get_current_screen_backend() == "rich"

        # Simulate switches at 1 and request app launch
        assert hardware.switches is not None
        # Use getattr to access mock-only helper without upsetting static typing
        simulate = getattr(hardware.switches, "simulate_switch_change", None)
        assert callable(simulate), "Mock switches missing simulate_switch_change"
        simulate(1)
        event_bus.publish("app_launch_requested", {}, "test")

        # During run (short delay), backend should be pillow
        import time
        deadline = time.time() + 1.0
        seen_pillow = False
        while time.time() < deadline:
            if hardware.get_current_screen_backend() == "pillow":
                seen_pillow = True
                break
            time.sleep(0.02)
        assert seen_pillow, "Expected backend to switch to pillow during app run"

        # After app finishes, backend should restore to rich
        deadline = time.time() + 2.0
        while time.time() < deadline:
            if hardware.get_current_screen_backend() == "rich":
                break
            time.sleep(0.02)
        assert hardware.get_current_screen_backend() == "rich"
    finally:
        # Stop system and event bus
        system.stop()
