"""
Test configuration and fixtures for BOSS tests.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add repository root to Python path so 'boss' package resolves
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import after path setup
from boss.core.models import BossConfig, HardwareConfig, SystemConfig
from boss.core import EventBus, AppManager, AppRunner, HardwareManager, SystemManager, AppAPI
from boss.hardware import (
    MockButtons, MockGoButton, MockLeds, MockSwitches, MockDisplay, MockScreen, MockSpeaker
)
from boss.hardware import MockHardwareFactory


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    hardware_config = HardwareConfig(
        switch_data_pin=18,
        switch_select_pins=[22, 23, 25],
        go_button_pin=16,
        button_pins={"red": 5, "yellow": 6, "green": 13, "blue": 19},
        led_pins={"red": 21, "yellow": 20, "green": 26, "blue": 12},
        display_clk_pin=2,
        display_dio_pin=3,
    screen_backend="rich",
        screen_width=800,
        screen_height=480,
        screen_fullscreen=True,
        enable_audio=True,
        audio_volume=0.7
    )
    
    system_config = SystemConfig(
        app_timeout_seconds=300,
        apps_directory="apps",
        log_level="INFO",
        log_file="logs/boss.log",
        log_max_size_mb=10,
        log_backup_count=5,
        event_queue_size=1000,
        event_timeout_seconds=1.0,
        webui_enabled=False,
        webui_host="localhost",
        webui_port=8080,
        enable_api=False,
        api_port=5000,
        auto_detect_hardware=True,
        force_hardware_type=None
    )
    
    return BossConfig(hardware=hardware_config, system=system_config)


@pytest.fixture
def mock_event_bus():
    """Create a mock event bus for testing."""
    return Mock(spec=EventBus)


# ----------------------------------------------------------------------------
# New standardized fixtures (preferred for new tests)
# ----------------------------------------------------------------------------

@pytest.fixture
def event_bus():
    """Real EventBus instance (started, auto-stopped)."""
    bus = EventBus(queue_size=256)
    bus.start()
    yield bus
    try:
        bus.stop()
    except Exception:
        pass


@pytest.fixture
def boss_config(mock_config):  # reuse existing mock_config
    """Alias to legacy mock_config for clearer naming in new tests."""
    return mock_config


@pytest.fixture
def hardware_factory(boss_config):
    """Mock hardware factory built from BossConfig."""
    return MockHardwareFactory(boss_config.hardware)


@pytest.fixture
def hardware_manager(hardware_factory, event_bus):
    """Initialized HardwareManager (not yet started monitoring)."""
    mgr = HardwareManager(hardware_factory, event_bus)
    mgr.initialize()
    return mgr


@pytest.fixture
def apps_dir(temp_apps_directory):  # reuse existing temp app scaffold
    return temp_apps_directory


@pytest.fixture
def app_manager(apps_dir, event_bus, hardware_manager, boss_config, tmp_path):
    """AppManager loaded with apps from apps_dir."""
    manager = AppManager(
        apps_directory=apps_dir,
        event_bus=event_bus,
        hardware_service=hardware_manager,
        config=boss_config,
        system_default_backend=getattr(boss_config.hardware, 'screen_backend', 'rich'),
    )
    # Point to app_mappings.json created by temp_apps_directory
    manager._app_mappings_file = tmp_path / "config" / "app_mappings.json"
    manager.load_apps()
    return manager


@pytest.fixture
def app_api_factory(event_bus, app_manager):
    """Factory producing AppAPI instances for given app name/path."""
    def _factory(name: str, path: Path):
        return AppAPI(event_bus=event_bus, app_name=name, app_path=path, app_manager=app_manager)
    return _factory


@pytest.fixture
def app_runner(event_bus, app_api_factory):
    return AppRunner(event_bus=event_bus, app_api_factory=app_api_factory)


@pytest.fixture
def system_manager(event_bus, hardware_manager, app_manager, app_runner):
    mgr = SystemManager(event_bus=event_bus, hardware_service=hardware_manager, app_manager=app_manager, app_runner=app_runner)
    return mgr


@pytest.fixture
def mock_hardware_factory():
    """Create a mock hardware factory with mock hardware components."""
    factory = Mock()
    factory.hardware_type = "mock"
    factory.create_buttons.return_value = MockButtons()
    factory.create_go_button.return_value = MockGoButton()
    factory.create_leds.return_value = MockLeds()
    factory.create_switches.return_value = MockSwitches()
    factory.create_display.return_value = MockDisplay()
    factory.create_screen.return_value = MockScreen()
    factory.create_speaker.return_value = MockSpeaker()
    return factory


@pytest.fixture
def temp_apps_directory(tmp_path):
    """Create a temporary apps directory for testing."""
    apps_dir = tmp_path / "apps"
    apps_dir.mkdir()
    
    # Create a test app
    test_app_dir = apps_dir / "test_app"
    test_app_dir.mkdir()
    
    # Create manifest
    manifest = test_app_dir / "manifest.json"
    manifest.write_text('''{
        "name": "Test App",
        "description": "A test application",
        "version": "1.0.0",
        "author": "Test Author",
        "entry_point": "main.py",
        "timeout_seconds": 60,
        "requires_network": false,
        "requires_audio": false,
        "tags": ["test"]
    }''')
    
    # Create main.py
    main_py = test_app_dir / "main.py"
    main_py.write_text('''def run(stop_event, api):
    """Test app main function."""
    api.log_info("Test app started")
    import time
    time.sleep(0.05)  # Brief delay to simulate work
    api.log_info("Test app finished")
''')
    
    # Create app_mappings.json in config directory
    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    app_mappings_file = config_dir / "app_mappings.json"
    app_mappings_file.write_text('''{"app_mappings": {"0": "test_app"}, "parameters": {}}''')
    
    return apps_dir


@pytest.fixture
def temp_config_directory(tmp_path):
    """Create a temporary config directory for testing."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    # Create boss_config.json
    boss_config = config_dir / "boss_config.json"
    boss_config.write_text('''{
        "hardware": {
            "switch_data_pin": 18,
            "button_pins": {"red": 5, "yellow": 6, "green": 13, "blue": 19},
            "led_pins": {"red": 21, "yellow": 20, "green": 26, "blue": 12},
            "display_clk_pin": 2,
            "display_dio_pin": 3,
            "screen_width": 800,
            "screen_height": 480,
            "enable_audio": true
        },
        "system": {
            "apps_directory": "apps",
            "log_level": "INFO",
            "app_timeout_seconds": 300
        }
    }''')
    
    # Create app_mappings.json
    app_mappings = config_dir / "app_mappings.json"
    app_mappings.write_text('''{
        "app_mappings": {
            "0": "test_app",
            "1": "hello_world"
        },
        "parameters": {}
    }''')
    
    return config_dir
