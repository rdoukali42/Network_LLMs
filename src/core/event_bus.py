"""
Event Bus for event-driven communication and loose coupling.
Provides publisher/subscriber pattern for system-wide event handling.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import inspect
import weakref

from utils.exceptions import EventError


class EventPriority(Enum):
    """Event priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """Event data structure."""
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventSubscription:
    """Event subscription information."""
    event_name: str
    handler: Callable
    subscriber_id: str
    is_async: bool = False
    once: bool = False
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventStats:
    """Event bus statistics."""
    total_events_published: int = 0
    total_events_handled: int = 0
    events_by_name: Dict[str, int] = field(default_factory=dict)
    handlers_by_event: Dict[str, int] = field(default_factory=dict)
    failed_handlers: int = 0
    average_handler_time: float = 0.0


class EventBus:
    """
    Event-driven communication bus for loose coupling between components.
    
    Features:
    - Publisher/subscriber pattern
    - Async and sync event handlers
    - Event filtering and routing
    - Priority-based event processing
    - Handler error isolation
    - Event replay and history
    - Performance monitoring
    """

    def __init__(self):
        """Initialize the Event Bus."""
        self.logger = logging.getLogger(__name__)
        
        # Subscriptions: event_name -> list of subscriptions
        self._subscriptions: Dict[str, List[EventSubscription]] = {}
        
        # Weak references to prevent memory leaks
        self._subscriber_refs: Dict[str, weakref.ref] = {}
        
        # Event queue for async processing
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Event history for replay
        self._event_history: List[Event] = []
        self._max_history_size = 1000
        
        # Statistics
        self._stats = EventStats()
        
        # Event filters
        self._global_filters: List[Callable[[Event], bool]] = []
        
        self.logger.info("Event Bus initialized")

    async def start(self):
        """Start the event bus processing."""
        if self._running:
            return
        
        self._running = True
        self._processing_task = asyncio.create_task(self._process_events())
        self.logger.info("Event Bus started")

    async def stop(self):
        """Stop the event bus processing."""
        if not self._running:
            return
        
        self._running = False
        
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Event Bus stopped")

    def subscribe(
        self,
        event_name: str,
        handler: Callable,
        subscriber_id: Optional[str] = None,
        once: bool = False,
        priority: int = 0
    ) -> str:
        """
        Subscribe to an event.
        
        Args:
            event_name: Name of the event to subscribe to
            handler: Handler function to call when event is published
            subscriber_id: Optional subscriber ID (auto-generated if not provided)
            once: Whether to unsubscribe after first event
            priority: Handler priority (higher numbers = higher priority)
            
        Returns:
            Subscription ID
            
        Raises:
            EventError: If subscription fails
        """
        try:
            # Generate subscriber ID if not provided
            if not subscriber_id:
                subscriber_id = f"{handler.__name__}_{id(handler)}"
            
            # Check if handler is async
            is_async = asyncio.iscoroutinefunction(handler)
            
            # Create subscription
            subscription = EventSubscription(
                event_name=event_name,
                handler=handler,
                subscriber_id=subscriber_id,
                is_async=is_async,
                once=once,
                priority=priority
            )
            
            # Add to subscriptions
            if event_name not in self._subscriptions:
                self._subscriptions[event_name] = []
            
            self._subscriptions[event_name].append(subscription)
            
            # Sort by priority (higher priority first)
            self._subscriptions[event_name].sort(key=lambda s: s.priority, reverse=True)
            
            # Store weak reference for cleanup
            self._subscriber_refs[subscriber_id] = weakref.ref(handler)
            
            self.logger.debug(f"Subscribed {subscriber_id} to event {event_name}")
            return subscriber_id
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe to event {event_name}: {str(e)}")
            raise EventError(f"Subscription failed: {str(e)}")

    def unsubscribe(self, event_name: str, subscriber_id: str) -> bool:
        """
        Unsubscribe from an event.
        
        Args:
            event_name: Event name
            subscriber_id: Subscriber ID
            
        Returns:
            True if successful
        """
        try:
            if event_name not in self._subscriptions:
                return False
            
            # Find and remove subscription
            subscriptions = self._subscriptions[event_name]
            original_length = len(subscriptions)
            
            self._subscriptions[event_name] = [
                sub for sub in subscriptions 
                if sub.subscriber_id != subscriber_id
            ]
            
            # Clean up if no more subscriptions
            if not self._subscriptions[event_name]:
                del self._subscriptions[event_name]
            
            # Remove weak reference
            if subscriber_id in self._subscriber_refs:
                del self._subscriber_refs[subscriber_id]
            
            success = len(subscriptions) < original_length
            if success:
                self.logger.debug(f"Unsubscribed {subscriber_id} from event {event_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to unsubscribe from event {event_name}: {str(e)}")
            return False

    def unsubscribe_all(self, subscriber_id: str) -> int:
        """
        Unsubscribe from all events for a subscriber.
        
        Args:
            subscriber_id: Subscriber ID
            
        Returns:
            Number of unsubscribed events
        """
        unsubscribed_count = 0
        
        for event_name in list(self._subscriptions.keys()):
            if self.unsubscribe(event_name, subscriber_id):
                unsubscribed_count += 1
        
        return unsubscribed_count

    async def publish(
        self,
        event_name: str,
        data: Optional[Dict[str, Any]] = None,
        priority: EventPriority = EventPriority.NORMAL,
        source: Optional[str] = None,
        correlation_id: Optional[str] = None,
        sync: bool = False
    ) -> bool:
        """
        Publish an event.
        
        Args:
            event_name: Name of the event
            data: Event data
            priority: Event priority
            source: Event source identifier
            correlation_id: Correlation ID for event tracking
            sync: Whether to process synchronously
            
        Returns:
            True if published successfully
            
        Raises:
            EventError: If publishing fails
        """
        try:
            # Create event
            event = Event(
                name=event_name,
                data=data or {},
                priority=priority,
                source=source,
                correlation_id=correlation_id
            )
            
            # Apply global filters
            for filter_func in self._global_filters:
                if not filter_func(event):
                    self.logger.debug(f"Event {event_name} filtered out")
                    return False
            
            # Add to history
            self._add_to_history(event)
            
            # Update stats
            self._stats.total_events_published += 1
            if event_name in self._stats.events_by_name:
                self._stats.events_by_name[event_name] += 1
            else:
                self._stats.events_by_name[event_name] = 1
            
            if sync:
                # Process synchronously
                await self._handle_event(event)
            else:
                # Add to queue for async processing
                await self._event_queue.put(event)
            
            self.logger.debug(f"Published event {event_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to publish event {event_name}: {str(e)}")
            raise EventError(f"Event publishing failed: {str(e)}")

    def publish_sync(
        self,
        event_name: str,
        data: Optional[Dict[str, Any]] = None,
        priority: EventPriority = EventPriority.NORMAL,
        source: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish an event synchronously.
        
        Args:
            event_name: Name of the event
            data: Event data
            priority: Event priority
            source: Event source identifier
            correlation_id: Correlation ID for event tracking
            
        Returns:
            True if published successfully
        """
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, create a task
                asyncio.create_task(self.publish(event_name, data, priority, source, correlation_id))
            else:
                # If we're not in an async context, run synchronously
                loop.run_until_complete(self.publish(event_name, data, priority, source, correlation_id))
            return True
        except Exception as e:
            self.logger.error(f"Failed to publish event {event_name}: {str(e)}")
            return False

    async def _process_events(self):
        """Process events from the queue."""
        while self._running:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._handle_event(event)
                self._event_queue.task_done()
                
            except asyncio.TimeoutError:
                # No events in queue, continue
                continue
            except asyncio.CancelledError:
                # Task cancelled, exit
                break
            except Exception as e:
                self.logger.error(f"Error processing event: {str(e)}")

    async def _handle_event(self, event: Event):
        """Handle a specific event by calling all subscribed handlers."""
        event_name = event.name
        
        if event_name not in self._subscriptions:
            return
        
        subscriptions = self._subscriptions[event_name].copy()
        handlers_called = 0
        
        for subscription in subscriptions:
            try:
                start_time = datetime.now()
                
                # Call handler
                if subscription.is_async:
                    await subscription.handler(event)
                else:
                    subscription.handler(event)
                
                # Update timing stats
                handler_time = (datetime.now() - start_time).total_seconds()
                self._update_handler_stats(handler_time)
                
                handlers_called += 1
                
                # Remove one-time subscriptions
                if subscription.once:
                    self.unsubscribe(event_name, subscription.subscriber_id)
                
            except Exception as e:
                self.logger.error(
                    f"Handler {subscription.subscriber_id} failed for event {event_name}: {str(e)}"
                )
                self._stats.failed_handlers += 1
        
        # Update stats
        self._stats.total_events_handled += 1
        if event_name in self._stats.handlers_by_event:
            self._stats.handlers_by_event[event_name] += handlers_called
        else:
            self._stats.handlers_by_event[event_name] = handlers_called

    def _add_to_history(self, event: Event):
        """Add event to history with size limit."""
        self._event_history.append(event)
        
        # Limit history size
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size:]

    def _update_handler_stats(self, handler_time: float):
        """Update handler timing statistics."""
        if self._stats.total_events_handled == 0:
            self._stats.average_handler_time = handler_time
        else:
            current_avg = self._stats.average_handler_time
            total_handled = self._stats.total_events_handled
            self._stats.average_handler_time = (
                (current_avg * total_handled + handler_time) / (total_handled + 1)
            )

    def add_global_filter(self, filter_func: Callable[[Event], bool]):
        """
        Add a global event filter.
        
        Args:
            filter_func: Function that returns True if event should be processed
        """
        self._global_filters.append(filter_func)
        self.logger.debug("Added global event filter")

    def remove_global_filter(self, filter_func: Callable[[Event], bool]) -> bool:
        """
        Remove a global event filter.
        
        Args:
            filter_func: Filter function to remove
            
        Returns:
            True if removed successfully
        """
        try:
            self._global_filters.remove(filter_func)
            self.logger.debug("Removed global event filter")
            return True
        except ValueError:
            return False

    def get_subscriptions(self, event_name: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get current subscriptions.
        
        Args:
            event_name: Specific event name or None for all
            
        Returns:
            Dictionary of event names to subscriber lists
        """
        if event_name:
            if event_name in self._subscriptions:
                return {
                    event_name: [sub.subscriber_id for sub in self._subscriptions[event_name]]
                }
            else:
                return {}
        
        # Return all subscriptions
        result = {}
        for event_name, subscriptions in self._subscriptions.items():
            result[event_name] = [sub.subscriber_id for sub in subscriptions]
        
        return result

    def get_event_history(
        self,
        event_name: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_name: Filter by event name
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        events = self._event_history
        
        # Filter by event name
        if event_name:
            events = [e for e in events if e.name == event_name]
        
        # Apply limit
        if limit:
            events = events[-limit:]
        
        return events

    def replay_events(
        self,
        event_name: Optional[str] = None,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None
    ) -> int:
        """
        Replay events from history.
        
        Args:
            event_name: Filter by event name
            from_time: Start time for replay
            to_time: End time for replay
            
        Returns:
            Number of events replayed
        """
        events_to_replay = self._event_history
        
        # Filter by event name
        if event_name:
            events_to_replay = [e for e in events_to_replay if e.name == event_name]
        
        # Filter by time range
        if from_time:
            events_to_replay = [e for e in events_to_replay if e.timestamp >= from_time]
        
        if to_time:
            events_to_replay = [e for e in events_to_replay if e.timestamp <= to_time]
        
        # Replay events
        replayed_count = 0
        for event in events_to_replay:
            try:
                asyncio.run(self._handle_event(event))
                replayed_count += 1
            except Exception as e:
                self.logger.error(f"Failed to replay event {event.name}: {str(e)}")
        
        self.logger.info(f"Replayed {replayed_count} events")
        return replayed_count

    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return {
            "total_events_published": self._stats.total_events_published,
            "total_events_handled": self._stats.total_events_handled,
            "events_by_name": dict(self._stats.events_by_name),
            "handlers_by_event": dict(self._stats.handlers_by_event),
            "failed_handlers": self._stats.failed_handlers,
            "average_handler_time": self._stats.average_handler_time,
            "total_subscriptions": sum(len(subs) for subs in self._subscriptions.values()),
            "unique_events": len(self._subscriptions),
            "event_history_size": len(self._event_history),
            "queue_size": self._event_queue.qsize() if self._event_queue else 0,
            "is_running": self._running
        }

    def clear_history(self):
        """Clear event history."""
        self._event_history.clear()
        self.logger.info("Event history cleared")

    def cleanup_dead_references(self) -> int:
        """
        Clean up subscriptions with dead weak references.
        
        Returns:
            Number of cleaned up subscriptions
        """
        cleaned_count = 0
        
        for event_name in list(self._subscriptions.keys()):
            original_count = len(self._subscriptions[event_name])
            
            # Filter out subscriptions with dead references
            self._subscriptions[event_name] = [
                sub for sub in self._subscriptions[event_name]
                if sub.subscriber_id in self._subscriber_refs and 
                self._subscriber_refs[sub.subscriber_id]() is not None
            ]
            
            # Remove empty event subscriptions
            if not self._subscriptions[event_name]:
                del self._subscriptions[event_name]
            
            cleaned_count += original_count - len(self._subscriptions.get(event_name, []))
        
        # Clean up dead weak references
        dead_refs = [
            ref_id for ref_id, ref in self._subscriber_refs.items()
            if ref() is None
        ]
        
        for ref_id in dead_refs:
            del self._subscriber_refs[ref_id]
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} dead subscription references")
        
        return cleaned_count


# Global event bus instance
_global_event_bus = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


async def publish_event(
    event_name: str,
    data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> bool:
    """Convenience function to publish an event using the global event bus."""
    event_bus = get_event_bus()
    return await event_bus.publish(event_name, data, **kwargs)


def subscribe_to_event(
    event_name: str,
    handler: Callable,
    **kwargs
) -> str:
    """Convenience function to subscribe to an event using the global event bus."""
    event_bus = get_event_bus()
    return event_bus.subscribe(event_name, handler, **kwargs)
