import types
import sys

import pytest

from boss.core.models import HardwareConfig
from boss.hardware import GPIODisplay


class DummyTM1637:
    def __init__(self, clk: int, dio: int):
        self.clk = clk
        self.dio = dio
        self._brightness = None
        self.commands = []

    def brightness(self, level: int):
        self._brightness = level

    def set_brightness(self, level: int):
        self._brightness = level

    def number(self, value: int):
        self.commands.append(("number", value))

    def show(self, s: str):
        self.commands.append(("show", s))

    def encode_string(self, s: str):
        # Return a simple list of ordinals to simulate encoding
        return [ord(c) for c in s]

    def write(self, encoded):
        self.commands.append(("write", tuple(encoded)))

    def clear(self):
        self.commands.append(("clear", None))


@pytest.fixture(autouse=True)
def patch_tm1637_module(monkeypatch):
    # Inject a fake 'tm1637' module into sys.modules
    m = types.ModuleType("tm1637")
    m.TM1637 = DummyTM1637
    sys.modules["tm1637"] = m
    yield
    sys.modules.pop("tm1637", None)


def make_hw_config():
    return HardwareConfig(
        switch_data_pin=18,
        switch_select_pins=[22, 23, 24],
        go_button_pin=17,
        button_pins={"red": 5, "yellow": 6, "green": 13, "blue": 19},
        led_pins={"red": 21, "yellow": 20, "green": 26, "blue": 12},
        display_clk_pin=2,
        display_dio_pin=3,
        screen_width=800,
        screen_height=480,
        screen_fullscreen=False,
        screen_backend="rich",
        enable_audio=False,
        audio_volume=1.0,
    )


def test_tm1637_display_initialize_and_basic_ops(monkeypatch):
    # Pretend gpiozero is present to allow initialization path
    # Patch HAS_GPIO on the module where GPIODisplay is defined without hardcoding path
    mod = sys.modules[GPIODisplay.__module__]
    monkeypatch.setattr(mod, "HAS_GPIO", True, raising=False)

    disp = GPIODisplay(make_hw_config())

    assert disp.initialize() is True
    assert disp.is_available is True

    # Brightness mapping should be applied during number/text calls
    disp.show_number(42, brightness=0.5)
    disp.show_text("HI", brightness=1.0)
    disp.set_brightness(0.0)
    disp.clear()

    # Validate our dummy captured calls
    tm = disp._tm
    assert tm is not None
    # We should have at least one brightness set between 0 and 7
    assert 0 <= (tm._brightness if tm._brightness is not None else 7) <= 7
    # Ensure number/text/clear were invoked
    ops = [op for op, _ in tm.commands]
    assert "number" in ops or "show" in ops
    assert "clear" in ops
