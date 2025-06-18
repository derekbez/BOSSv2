import time
import types
from boss.core.app_runner import AppRunner

# Dummy app for testing
class DummyApp:
    def __init__(self):
        self.stopped = False
    def run(self, stop_event, api):
        while not stop_event.is_set():
            time.sleep(0.01)
        self.stopped = True

def test_app_runner_starts_and_stops(monkeypatch):
    runner = AppRunner(timeout=1)
    dummy = DummyApp()
    # Patch importlib to return dummy app
    monkeypatch.setattr("importlib.import_module", lambda name: types.SimpleNamespace(run=dummy.run))
    runner.run_app("dummy")
    time.sleep(0.05)
    assert runner.app_thread.is_alive()
    runner.stop_app()
    assert not runner.app_thread
    assert dummy.stopped

def test_app_runner_forced_termination(monkeypatch):
    runner = AppRunner(timeout=0.1)
    # App that never stops
    def never_stops(stop_event, api):
        while True:
            time.sleep(0.01)
    monkeypatch.setattr("importlib.import_module", lambda name: types.SimpleNamespace(run=never_stops))
    runner.run_app("never_stops")
    time.sleep(0.05)
    runner.stop_app()
    # Thread may still be alive, but error should be logged
