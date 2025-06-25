from boss.hardware.screen import MockScreen
import pytest

def test_mock_screen_status_and_output():
    screen = MockScreen()
    screen.show_status("Ready")
    assert screen.last_status == "Ready"
    screen.show_app_output("App running!")
    assert screen.last_output == "App running!"

def test_mock_screen_clear():
    screen = MockScreen()
    screen.show_status("Test")
    screen.show_app_output("Test output")
    screen.clear()
    assert screen.last_status is None
    assert screen.last_output is None

def test_mock_screen_display_text_basic():
    screen = MockScreen()
    screen.display_text("Hello world!")
    assert screen.last_output == "Hello world!"

def test_mock_screen_display_text_advanced():
    screen = MockScreen()
    # Should not raise with advanced kwargs
    screen.display_text(
        "Advanced!",
        align='center',
        color=(255,0,0),
        size=32,
        bold=True,
        italic=True,
        underline=True,
        shadow=((2,2),(0,0,0)),
        wrap=100,
        opacity=128,
        outline=((0,255,0),2),
        font_name="Arial"
    )
    assert screen.last_output == "Advanced!"
