from boss.hardware.led import MockLED

def test_mock_led():
    led = MockLED('red')
    assert not led.state
    led.set_state(True)
    assert led.state
    led.set_state(False)
    assert not led.state
