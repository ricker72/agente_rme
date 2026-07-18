"""
RULE-41 event subscriber primitives.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Optional

from .event_models import EventCategory, GenerationEvent, normalize_event_category

EventHandler = Callable[[GenerationEvent], None]


@dataclass(frozen=True)
class EventSubscriber:
    """A synchronous subscriber registered with the observability bus."""

    name: str
    handler: EventHandler
    categories: Optional[set[EventCategory]] = None

    def accepts(self, event: GenerationEvent) -> bool:
        """Return True when this subscriber wants the event."""
        return self.categories is None or event.category in self.categories


def normalize_categories(
    categories: Optional[Iterable[EventCategory | str]],
) -> Optional[set[EventCategory]]:
    """Normalize an optional category filter."""
    if categories is None:
        return None
    return {normalize_event_category(category) for category in categories}
