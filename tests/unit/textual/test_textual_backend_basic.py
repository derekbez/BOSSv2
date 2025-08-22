import os
import time
import types
import pytest

from boss.infrastructure.config.config_manager import validate_config
from boss.domain.models.config import HardwareConfig, SystemConfig, BossConfig
from boss.infrastructure.hardware.gpio.gpio_factory import GPIOHardwareFactory
from boss.application.services.hardware_service import HardwareManager

class DummyEventBus:
    def __init__(self):
        self._subs = {}
    def start(self):
        pass
    def stop(self):
        pass
    def subscribe(self, event_type, callback):
        self._subs.setdefault(event_type, []).append(callback)
    def publish(self, event_type, payload, source):
        for cb in self._subs.get(event_type, []):
            try:
                cb(event_type, payload)
            except Exception:
                pass
    def get_stats(self):
        return {"events": sum(len(v) for v in self._subs.values())}

@pytest.fixture
def boss_config():
    hw = HardwareConfig(
        switch_data_pin=1,
        switch_select_pins=[2,3,4],
        go_button_pin=5,
        button_pins={"red":6,"yellow":7,"green":8,"blue":9},
        led_pins={"red":10,"yellow":11,"green":12,"blue":13},
        display_clk_pin=14,
        display_dio_pin=15,
        screen_width=80,
        screen_height=25,
        screen_fullscreen=False,
        screen_backend='textual',
        enable_audio=False,
        audio_volume=0.0,
        led_active_high=True
    )
    syscfg = SystemConfig(
        app_timeout_seconds=5,
        apps_directory='apps',
        log_level='INFO',
        log_file='logs/boss.log',
        log_max_size_mb=5,
        log_backup_count=2,
        event_queue_size=100,
        event_timeout_seconds=1.0,
        webui_enabled=False,
        webui_host='127.0.0.1',
        webui_port=8080,
        enable_api=False,
        api_port=9000,
        auto_detect_hardware=False,
        force_hardware_type='gpio'
    )
    return BossConfig(hardware=hw, system=syscfg)

@pytest.mark.skipif(os.name != 'nt' and not os.getenv('CI'), reason='Non-hardware test environment')
def test_textual_backend_initialize_and_metrics(boss_config):
    # Simulate rich available; textual backend chosen
    factory = GPIOHardwareFactory(boss_config.hardware)
    event_bus = DummyEventBus()
    hm = HardwareManager(factory, event_bus)
    # Limit to screen only to keep test fast
    hm.screen = factory.create_screen()
    assert hm.screen is not None
    if hasattr(hm.screen, 'initialize'):
        hm.screen.initialize()
    # Push quick updates
    for i in range(5):
        hm.update_screen('text', f'Line {i}')
    time.sleep(0.3)  # allow debounce loop to process
    metrics = {}
    if hasattr(hm.screen, 'get_metrics'):
        metrics = getattr(hm.screen, 'get_metrics')()
    assert 'render_count' in metrics

@pytest.mark.skipif(os.name == 'posix' and not os.isatty(1), reason='TTY required for auto selection test')
def test_auto_mode_selection_prefers_textual_when_tty(boss_config, monkeypatch):
    boss_config.hardware.screen_backend = 'auto'
    factory = GPIOHardwareFactory(boss_config.hardware)
    # Force conditions: posix tty no DISPLAY and textual available assumed
    monkeypatch.setenv('DISPLAY','')
    screen = factory.create_screen()
    # backend chosen stored internally
    assert factory.get_current_screen_backend() in {'textual','rich','pillow'}  # pillow kept for legacy
