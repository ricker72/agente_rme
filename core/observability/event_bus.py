"""
RULE-41 live generation event bus.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Iterable, Optional

from .event_models import EventCategory, GenerationEvent
from .event_storage import EventStorage
from .event_subscriber import EventHandler, EventSubscriber, normalize_categories


class EventBus:
    """Thread-safe synchronous bus for generation events."""

    def __init__(self, storage: Optional[EventStorage] = None) -> None:
        self.storage = storage or EventStorage()
        self._lock = threading.Lock()
        self._subscribers: dict[str, EventSubscriber] = {}
        self.events_consumed = 0

    def subscribe(
        self,
        name: str,
        handler: EventHandler,
        categories: Optional[Iterable[EventCategory | str]] = None,
    ) -> None:
        """Register a subscriber."""
        subscriber = EventSubscriber(
            name=name,
            handler=handler,
            categories=normalize_categories(categories),
        )
        with self._lock:
            self._subscribers[name] = subscriber

    def unsubscribe(self, name: str) -> None:
        """Remove a subscriber."""
        with self._lock:
            self._subscribers.pop(name, None)

    def publish(self, event: GenerationEvent) -> GenerationEvent:
        """Persist and fan out one event."""
        self.storage.persist(event)
        with self._lock:
            subscribers = list(self._subscribers.values())
        for subscriber in subscribers:
            if subscriber.accepts(event):
                subscriber.handler(event)
                self.events_consumed += 1
        return event

    def reset(self) -> None:
        """Clear subscribers and storage."""
        with self._lock:
            self._subscribers = {}
            self.events_consumed = 0
        self.storage.reset()


_DEFAULT_BUS: Optional[EventBus] = None
_DEFAULT_LOCK = threading.Lock()


def get_event_bus(workspace_root: Optional[Path] = None) -> EventBus:
    """Return the singleton RULE-41 event bus."""
    global _DEFAULT_BUS
    with _DEFAULT_LOCK:
        if _DEFAULT_BUS is None:
            _DEFAULT_BUS = EventBus(EventStorage(workspace_root))
    return _DEFAULT_BUS


def reset_event_bus(workspace_root: Optional[Path] = None) -> EventBus:
    """Reset and return the singleton event bus."""
    global _DEFAULT_BUS
    with _DEFAULT_LOCK:
        _DEFAULT_BUS = EventBus(EventStorage(workspace_root))
    return _DEFAULT_BUS
