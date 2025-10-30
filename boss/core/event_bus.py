"""
Simple, robust event bus for B.O.S.S.
"""

import logging
import threading
import queue
import time
import uuid
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from boss.core.events.domain_events import DomainEvent


logger = logging.getLogger(__name__)


@dataclass
class Subscription:
    """Event subscription."""
    id: str
    event_type: str
    handler: Callable
    filter_dict: Optional[Dict[str, Any]] = None


class EventBus:
    """
    Simple, robust event bus for BOSS.
    
    Features:
    - Thread-safe event publishing and subscription
    - Event filtering
    - Automatic cleanup of failed handlers
    - Simple logging for debugging
    """
    
    def __init__(self, queue_size: int = 1000):
        self._subscriptions: Dict[str, List[Subscription]] = {}
        self._event_queue = queue.Queue(maxsize=queue_size)
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.RLock()
        
    def start(self) -> None:
        """Start the event bus processing thread."""
        with self._lock:
            if self._running:
                return
                
            self._running = True
            self._worker_thread = threading.Thread(target=self._process_events, daemon=True)
            self._worker_thread.start()
            logger.info("Event bus started")
    
    def stop(self) -> None:
        """Stop the event bus."""
        with self._lock:
            if not self._running:
                return
                
            self._running = False
            
            # Signal worker thread to stop
            try:
                self._event_queue.put(None, timeout=1.0)
            except queue.Full:
                pass
            
            # Wait for worker thread to finish
            if self._worker_thread and self._worker_thread.is_alive():
                self._worker_thread.join(timeout=2.0)
            
            logger.info("Event bus stopped")
    
    def publish(self, event_type: str, payload: Dict[str, Any], source: str = "system") -> None:
        """
        Publish an event.
        
        Args:
            event_type: Type of event
            payload: Event data
            source: Source of the event
        """
        if not self._running:
            logger.warning(f"Event bus not running, dropping event: {event_type}")
            return
        
        event = DomainEvent(
            event_type=event_type,
            timestamp=time.time(),
            payload=payload,
            source=source
        )
        
        try:
            self._event_queue.put(event, timeout=1.0)
            logger.debug(f"Published event: {event_type} from {source}")
        except queue.Full:
            logger.error(f"Event queue full, dropping event: {event_type}")
    
    def subscribe(self, event_type: str, handler: Callable, filter_dict: Optional[Dict[str, Any]] = None) -> str:
        """
        Subscribe to events.
        
        Args:
            event_type: Type of events to subscribe to
            handler: Callback function to handle events
            filter_dict: Optional filter for event payload
            
        Returns:
            Subscription ID for unsubscribing
        """
        subscription_id = str(uuid.uuid4())
        subscription = Subscription(
            id=subscription_id,
            event_type=event_type,
            handler=handler,
            filter_dict=filter_dict
        )
        
        with self._lock:
            if event_type not in self._subscriptions:
                self._subscriptions[event_type] = []
            self._subscriptions[event_type].append(subscription)
        
        logger.debug(f"Subscribed to {event_type} with ID {subscription_id}")
        return subscription_id
    
    def unsubscribe(self, subscription_id: str) -> None:
        """
        Unsubscribe from events.
        
        Args:
            subscription_id: ID returned from subscribe()
        """
        with self._lock:
            for event_type, subscriptions in self._subscriptions.items():
                self._subscriptions[event_type] = [
                    sub for sub in subscriptions if sub.id != subscription_id
                ]
        
        logger.debug(f"Unsubscribed {subscription_id}")
    
    def _process_events(self) -> None:
        """Process events in worker thread."""
        logger.info("Event bus worker thread started")
        
        while self._running:
            try:
                # Get event from queue with timeout
                event = self._event_queue.get(timeout=1.0)
                
                # None signals shutdown
                if event is None:
                    break
                
                self._handle_event(event)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
        
        logger.info("Event bus worker thread stopped")
    
    def _handle_event(self, event: DomainEvent) -> None:
        """Handle a single event by calling all matching subscribers."""
        with self._lock:
            subscriptions = self._subscriptions.get(event.event_type, [])
        
        if not subscriptions:
            logger.debug(f"No subscribers for event: {event.event_type}")
            return
        
        # Call each subscriber
        failed_subscriptions = []
        for subscription in subscriptions:
            try:
                # Check if event matches filter
                if self._matches_filter(event, subscription.filter_dict):
                    subscription.handler(event.event_type, event.payload)
                    logger.debug(f"Handled event {event.event_type} with subscription {subscription.id}")
                
            except Exception as e:
                logger.error(f"Error in event handler {subscription.id} for {event.event_type}: {e}")
                failed_subscriptions.append(subscription)
        
        # Remove failed subscriptions
        if failed_subscriptions:
            with self._lock:
                for failed_sub in failed_subscriptions:
                    try:
                        self._subscriptions[event.event_type].remove(failed_sub)
                        logger.warning(f"Removed failed subscription {failed_sub.id}")
                    except ValueError:
                        pass  # Already removed
    
    def _matches_filter(self, event: DomainEvent, filter_dict: Optional[Dict[str, Any]]) -> bool:
        """Check if event matches subscription filter."""
        if filter_dict is None:
            return True
        
        for key, value in filter_dict.items():
            if key not in event.payload or event.payload[key] != value:
                return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        with self._lock:
            subscription_count = sum(len(subs) for subs in self._subscriptions.values())
            return {
                "running": self._running,
                "queue_size": self._event_queue.qsize(),
                "subscription_count": subscription_count,
                "event_types": list(self._subscriptions.keys())
            }
