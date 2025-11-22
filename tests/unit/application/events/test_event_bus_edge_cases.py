import time
import pytest
from boss.core.event_bus import EventBus


def test_event_bus_filtering_and_failed_handler_removal():
    bus = EventBus(queue_size=10)
    received = []
    def handler_all(t, p):
        received.append((t, p))
    def handler_filtered(t, p):
        received.append((t, p, 'filtered'))
    # Failing handler to ensure automatic removal
    calls = {'count': 0}
    def handler_fail(t, p):
        calls['count'] += 1
        raise RuntimeError('boom')

    bus.subscribe('demo', handler_all)
    bus.subscribe('demo', handler_filtered, filter_dict={'x': 1})
    fail_id = bus.subscribe('demo', handler_fail)
    bus.start()
    # First publish triggers failure removal
    bus.publish('demo', {'x': 1})
    # Second publish should not invoke failing handler again
    bus.publish('demo', {'x': 2})
    time.sleep(0.2)
    bus.stop()
    # handler_fail called only once then removed
    assert calls['count'] == 1
    # filtering: one filtered entry for first event only
    filtered = [r for r in received if len(r) == 3 and r[2] == 'filtered']
    assert len(filtered) == 1
    # handler_all received both events
    all_events = [r for r in received if len(r) == 2]
    assert len(all_events) == 2


def test_pre_start_publish_queueing():
    bus = EventBus(queue_size=5)
    received = []
    bus.subscribe('queued', lambda t, p: received.append(p))
    # Publish before start
    bus.publish('queued', {'a': 1})
    bus.publish('queued', {'b': 2})
    assert received == []  # not processed yet
    bus.start()
    # Give processing time
    time.sleep(0.15)
    bus.stop()
    # Both events processed after start
    assert {'a': 1} in received and {'b': 2} in received


def test_unsubscribe_nonexistent_id_is_noop():
    bus = EventBus()
    bus.unsubscribe('not-a-real-id')  # Should not raise
    bus.start()
    bus.stop()
