from boss.hardware.screen import MockScreen

def test_mock_screen_status_and_output():
    screen = MockScreen()
    screen.show_status("Ready")
    assert screen.last_status == "Ready"
    screen.show_app_output("App running!")
    assert screen.last_output == "App running!"
