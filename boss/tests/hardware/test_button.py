from boss.hardware.button import MockButton

def test_mock_button_press_and_release():
    button = MockButton('go')
    pressed = []
    def cb():
        pressed.append(True)
    button.set_callback(cb)
    assert not button.is_pressed()
    button.press()
    assert button.is_pressed()
    assert pressed == [True]
    button.release()
    assert not button.is_pressed()
