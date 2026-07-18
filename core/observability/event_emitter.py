"""
RULE-41 generation event emitter helpers.
"""

from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from typing import Any, Dict, Iterator, Optional

from .event_bus import EventBus, get_event_bus
from .event_models import EventCategory, EventSeverity, GenerationEvent


class EventEmitter:
    """Small producer API used by generation modules."""

    def __init__(self, module: str, bus: Optional[EventBus] = None) -> None:
        self.module = module
        self.bus = bus or get_event_bus()

    def emit(
        self,
        *,
        trace_id: str,
        phase: str,
        action: str,
        description: str,
        category: EventCategory | str,
        entity_type: str,
        result: str = "PASS",
        coordinates: Optional[Dict[str, int]] = None,
        floor: Optional[int] = None,
        severity: EventSeverity | str = EventSeverity.INFO,
        duration_ms: float = 0.0,
        parent_event: Optional[str] = None,
        source_dataset: Optional[str] = None,
        reasoning_chain: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GenerationEvent:
        """Create, validate, persist, and publish one generation event."""
        event = GenerationEvent(
            module=self.module,
            phase=phase,
            action=action,
            description=description,
            category=category,
            entity_type=entity_type,
            result=result,
            trace_id=trace_id,
            coordinates=coordinates,
            floor=floor,
            severity=severity,
            duration_ms=duration_ms,
            parent_event=parent_event,
            source_dataset=source_dataset,
            reasoning_chain=reasoning_chain or [],
            metadata=metadata or {},
        )
        return self.bus.publish(event)

    @contextmanager
    def timed_event(self, **event_fields: Any) -> Iterator[Dict[str, Any]]:
        """Emit one event with measured duration on context exit."""
        metadata: Dict[str, Any] = event_fields.pop("metadata", {}) or {}
        started = perf_counter()
        result = event_fields.pop("result", "PASS")
        severity = event_fields.pop("severity", EventSeverity.INFO)
        try:
            yield metadata
        except Exception as exc:
            result = "ERROR"
            severity = EventSeverity.ERROR
            metadata["exception"] = repr(exc)
            raise
        finally:
            duration_ms = (perf_counter() - started) * 1000.0
            self.emit(
                **event_fields,
                result=result,
                severity=severity,
                duration_ms=duration_ms,
                metadata=metadata,
            )


def emit_generation_event(module: str, **event_fields: Any) -> GenerationEvent:
    """Convenience producer entry point for generation modules."""
    return EventEmitter(module).emit(**event_fields)
