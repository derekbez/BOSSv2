"""
Unit tests for EventBus.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch

from boss.application.events.event_bus import EventBus


class TestEventBus:
    """Test cases for EventBus."""
    
    def test_init(self):
        """Test EventBus initialization."""
        event_bus = EventBus(queue_size=500)
        
        assert event_bus._event_queue.maxsize == 500
        assert event_bus._running is False
        assert event_bus._subscriptions == {}
    
    def test_start_stop(self):
        """Test starting and stopping the event bus."""
        event_bus = EventBus()
        
        assert not event_bus._running
        
        event_bus.start()
        assert event_bus._running
        assert event_bus._worker_thread is not None
        assert event_bus._worker_thread.is_alive()
        
        event_bus.stop()
        assert not event_bus._running
        # Give worker thread time to stop
        time.sleep(0.1)
        assert not event_bus._worker_thread.is_alive()
    
    def test_subscribe_unsubscribe(self):
        """Test subscribing and unsubscribing from events."""
        event_bus = EventBus()
        handler = Mock()
        
        # Subscribe
        subscription_id = event_bus.subscribe("test_event", handler)
        
        assert "test_event" in event_bus._subscriptions
        assert len(event_bus._subscriptions["test_event"]) == 1
        assert event_bus._subscriptions["test_event"][0].id == subscription_id
        assert event_bus._subscriptions["test_event"][0].handler == handler
        
        # Unsubscribe
        event_bus.unsubscribe(subscription_id)
        assert len(event_bus._subscriptions["test_event"]) == 0
    
    def test_subscribe_with_filter(self):
        """Test subscribing with event filter."""
        event_bus = EventBus()
        handler = Mock()
        filter_dict = {"button": "red"}
        
        subscription_id = event_bus.subscribe("button_pressed", handler, filter_dict)
        
        subscription = event_bus._subscriptions["button_pressed"][0]
        assert subscription.filter_dict == filter_dict
    
    def test_publish_and_handle_event(self):
        """Test publishing and handling events."""
        event_bus = EventBus()
        event_bus.start()
        
        handler = Mock()
        event_bus.subscribe("test_event", handler)
        
        # Publish event
        payload = {"test": "data"}
        event_bus.publish("test_event", payload)
        
        # Give worker thread time to process
        time.sleep(0.1)
        
        handler.assert_called_once_with("test_event", payload)
        
        event_bus.stop()
    
    def test_event_filtering(self):
        """Test event filtering functionality."""
        event_bus = EventBus()
        event_bus.start()
        
        handler1 = Mock()
        handler2 = Mock()
        
        # Subscribe with different filters
        event_bus.subscribe("button_pressed", handler1, {"button": "red"})
        event_bus.subscribe("button_pressed", handler2, {"button": "blue"})
        
        # Publish red button event
        event_bus.publish("button_pressed", {"button": "red", "timestamp": 123})
        time.sleep(0.1)
        
        # Only handler1 should be called
        handler1.assert_called_once_with("button_pressed", {"button": "red", "timestamp": 123})
        handler2.assert_not_called()
        
        # Reset mocks
        handler1.reset_mock()
        handler2.reset_mock()
        
        # Publish blue button event
        event_bus.publish("button_pressed", {"button": "blue", "timestamp": 456})
        time.sleep(0.1)
        
        # Only handler2 should be called
        handler1.assert_not_called()
        handler2.assert_called_once_with("button_pressed", {"button": "blue", "timestamp": 456})
        
        event_bus.stop()
    
    def test_event_filtering_no_filter(self):
        """Test that handlers without filters receive all events."""
        event_bus = EventBus()
        event_bus.start()
        
        handler_all = Mock()
        handler_filtered = Mock()
        
        # Subscribe without filter and with filter
        event_bus.subscribe("button_pressed", handler_all)
        event_bus.subscribe("button_pressed", handler_filtered, {"button": "red"})
        
        # Publish events
        event_bus.publish("button_pressed", {"button": "red"})
        event_bus.publish("button_pressed", {"button": "blue"})
        time.sleep(0.1)
        
        # handler_all should receive both events
        assert handler_all.call_count == 2
        # handler_filtered should only receive red button event
        assert handler_filtered.call_count == 1
        
        event_bus.stop()
    
    def test_handler_exception_handling(self):
        """Test that handler exceptions don't crash the event bus."""
        event_bus = EventBus()
        event_bus.start()
        
        def failing_handler(event_type, payload):
            raise Exception("Handler failed")
        
        working_handler = Mock()
        
        event_bus.subscribe("test_event", failing_handler)
        event_bus.subscribe("test_event", working_handler)
        
        with patch('boss.application.events.event_bus.logger') as mock_logger:
            event_bus.publish("test_event", {"test": "data"})
            time.sleep(0.1)
            
            # Working handler should still be called
            working_handler.assert_called_once()
            # Error should be logged
            mock_logger.error.assert_called()
        
        event_bus.stop()
    
    def test_get_stats(self):
        """Test getting event bus statistics."""
        event_bus = EventBus()
        
        # Subscribe some handlers
        event_bus.subscribe("event1", Mock())
        event_bus.subscribe("event2", Mock())
        event_bus.subscribe("event1", Mock())
        
        stats = event_bus.get_stats()
        
        assert stats["subscription_count"] == 3
        assert "event1" in stats["event_types"]
        assert "event2" in stats["event_types"]
        assert stats["running"] is False
        assert stats["queue_size"] == 0
    
    def test_multiple_subscriptions_same_event(self):
        """Test multiple subscriptions to the same event type."""
        event_bus = EventBus()
        event_bus.start()
        
        handler1 = Mock()
        handler2 = Mock()
        handler3 = Mock()
        
        event_bus.subscribe("test_event", handler1)
        event_bus.subscribe("test_event", handler2)
        event_bus.subscribe("test_event", handler3)
        
        event_bus.publish("test_event", {"data": "test"})
        time.sleep(0.1)
        
        # All handlers should be called
        handler1.assert_called_once_with("test_event", {"data": "test"})
        handler2.assert_called_once_with("test_event", {"data": "test"})
        handler3.assert_called_once_with("test_event", {"data": "test"})
        
        event_bus.stop()
    
    def test_unsubscribe_invalid_id(self):
        """Test unsubscribing with invalid subscription ID."""
        event_bus = EventBus()
        
        # Should not raise exception
        event_bus.unsubscribe("invalid-id")
        event_bus.unsubscribe("99999")
    
    def test_start_stop_lifecycle(self):
        """Test EventBus start/stop lifecycle."""
        event_bus = EventBus()
        
        # Test start
        event_bus.start()
        assert event_bus._running
        
        handler = Mock()
        event_bus.subscribe("test_event", handler)
        event_bus.publish("test_event", {"test": "data"})
        
        time.sleep(0.1)
        handler.assert_called_once()
        
        # Test stop
        event_bus.stop()
        assert not event_bus._running
