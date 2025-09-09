import threading
import time
from boss.application.services.app_runner import AppRunner
from boss.domain.models.app import App, AppManifest


class DummyEventBus:
    def __init__(self):
        self.events = []

    def publish(self, name, payload, source):
        self.events.append((name, payload, source))

    def subscribe(self, *a, **k):
        return "sub"

    def unsubscribe(self, *a, **k):
        pass


def make_app(manifest: AppManifest, tmp_path):
    # create a fake app dir with a main.py that honors stop_event
    app_dir = tmp_path / manifest.name
    app_dir.mkdir()
    main = app_dir / "main.py"
    main.write_text(
        """
import time

def run(stop_event, api):
    # run until stop_event set
    while not stop_event.is_set():
        time.sleep(0.05)
"""
    )
    return App(switch_value=1, manifest=manifest, app_path=app_dir)


def test_return_on_timeout(tmp_path):
    # App with short timeout and default 'return' behavior
    manifest = AppManifest(name="t1", description="x", version="1", author="a", timeout_seconds=1, timeout_behavior="return")
    app = make_app(manifest, tmp_path)
    bus = DummyEventBus()
    runner = AppRunner(bus, lambda n, p: None)
    runner.start_app(app)
    time.sleep(1.5)
    # wait a moment for events
    time.sleep(0.2)
    # Expect app_stopped and return_to_startup
    names = [e[0] for e in bus.events]
    assert "app_stopped" in names
    assert any(e[0] == "return_to_startup" for e in bus.events)


def test_rerun_on_timeout(tmp_path):
    manifest = AppManifest(name="t2", description="x", version="1", author="a", timeout_seconds=1, timeout_behavior="rerun")
    app = make_app(manifest, tmp_path)
    bus = DummyEventBus()
    started = []

    def factory(name, path):
        # return a dummy api
        started.append(name)
        return None

    runner = AppRunner(bus, factory)
    runner.start_app(app)
    time.sleep(1.5)
    time.sleep(0.2)
    # after timeout, runner should have attempted to start again
    assert len([e for e in bus.events if e[0] == 'app_stopped']) >= 1
    # we also expect start_app to have been invoked again (factory called)
    assert started.count(manifest.name) >= 2


def test_none_on_timeout(tmp_path):
    manifest = AppManifest(name="t3", description="x", version="1", author="a", timeout_seconds=1, timeout_behavior="none")
    app = make_app(manifest, tmp_path)
    bus = DummyEventBus()
    runner = AppRunner(bus, lambda n, p: None)
    runner.start_app(app)
    time.sleep(1.5)
    time.sleep(0.2)
    # app_stopped should still be published but no return_to_startup
    names = [e[0] for e in bus.events]
    assert "app_stopped" in names
    assert not any(e[0] == "return_to_startup" for e in bus.events)
