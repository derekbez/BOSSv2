import time
from boss.core import AppRunner
from boss.core.models import App, AppManifest
from pathlib import Path


class DummyEventBus:
    def __init__(self):
        self.events = []
    def publish(self, name, payload, source):
        self.events.append((name, payload, source))
    def subscribe(self, *a, **k):
        return 'sub'
    def unsubscribe(self, *a, **k):
        pass


def make_app(manifest: AppManifest, tmp_path):
    app_dir = tmp_path / manifest.name
    app_dir.mkdir()
    (app_dir / 'main.py').write_text('import time\n\n' 'def run(stop_event, api):\n' '  while not stop_event.is_set():\n' '    time.sleep(0.05)\n')
    return App(switch_value=1, manifest=manifest, app_path=app_dir)


def test_timeout_default_rerun_for_network_tag(tmp_path):
    # Explicitly set timeout_behavior None to trigger tag-based default rerun
    manifest = AppManifest(name='net_app', description='x', version='1', author='a', timeout_seconds=1, tags=['network'], timeout_behavior=None)
    bus = DummyEventBus()
    runner = AppRunner(bus, lambda n, p: None)
    app = make_app(manifest, tmp_path)
    runner.start_app(app)
    # Wait for timeout (1s) + default cooldown (1s) + margin
    time.sleep(2.5)
    started_events = [e for e in bus.events if e[0] == 'app_started']
    assert len(started_events) >= 2


def test_timeout_default_return_for_non_network_tag(tmp_path):
    manifest = AppManifest(name='plain_app', description='x', version='1', author='a', timeout_seconds=1, tags=['utility'])
    bus = DummyEventBus()
    runner = AppRunner(bus, lambda n, p: None)
    app = make_app(manifest, tmp_path)
    runner.start_app(app)
    time.sleep(1.4)
    time.sleep(0.2)
    # Expect app_stopped and a return_to_startup event
    assert any(e[0] == 'app_stopped' and e[1].get('reason') == 'timeout' for e in bus.events)
    assert any(e[0] == 'return_to_startup' for e in bus.events)
