"""
RULE-41 live generation observability event models.

Every important world-generation decision is represented as a structured
GenerationEvent before it can be persisted or consumed by UI systems.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4


class EventCategory(str, Enum):
    ARCHITECTURE_EVENT = "ARCHITECTURE_EVENT"
    TILE_PLACEMENT_EVENT = "TILE_PLACEMENT_EVENT"
    BRUSH_SELECTION_EVENT = "BRUSH_SELECTION_EVENT"
    APPEARANCE_SELECTION_EVENT = "APPEARANCE_SELECTION_EVENT"
    DISTRICT_EVENT = "DISTRICT_EVENT"
    ROAD_EVENT = "ROAD_EVENT"
    BUILDING_EVENT = "BUILDING_EVENT"
    TEMPLE_EVENT = "TEMPLE_EVENT"
    DEPOT_EVENT = "DEPOT_EVENT"
    HOUSE_EVENT = "HOUSE_EVENT"
    SHOP_EVENT = "SHOP_EVENT"
    NPC_EVENT = "NPC_EVENT"
    SPAWN_EVENT = "SPAWN_EVENT"
    QUEST_EVENT = "QUEST_EVENT"
    INTERACTION_EVENT = "INTERACTION_EVENT"
    CONNECTIVITY_EVENT = "CONNECTIVITY_EVENT"
    PLAYABILITY_EVENT = "PLAYABILITY_EVENT"
    VALIDATION_EVENT = "VALIDATION_EVENT"
    EXPORT_EVENT = "EXPORT_EVENT"
    ERROR_EVENT = "ERROR_EVENT"
    WARNING_EVENT = "WARNING_EVENT"


class EventSeverity(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


MANDATORY_EVENT_FIELDS = (
    "event_id",
    "trace_id",
    "timestamp",
    "module",
    "phase",
    "action",
    "description",
    "coordinates",
    "floor",
    "entity_type",
    "severity",
    "result",
    "duration_ms",
    "parent_event",
    "source_dataset",
)


def utc_timestamp() -> str:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def normalize_event_category(value: EventCategory | str) -> EventCategory:
    """Normalize a category string into an EventCategory."""
    if isinstance(value, EventCategory):
        return value
    return EventCategory(value)


def normalize_event_severity(value: EventSeverity | str) -> EventSeverity:
    """Normalize a severity string into an EventSeverity."""
    if isinstance(value, EventSeverity):
        return value
    return EventSeverity(value)


@dataclass(frozen=True)
class GenerationEvent:
    """Canonical RULE-41 event payload."""

    module: str
    phase: str
    action: str
    description: str
    entity_type: str
    category: EventCategory | str
    result: str
    trace_id: str
    coordinates: Optional[Dict[str, int]] = None
    floor: Optional[int] = None
    severity: EventSeverity | str = EventSeverity.INFO
    duration_ms: float = 0.0
    parent_event: Optional[str] = None
    source_dataset: Optional[str] = None
    reasoning_chain: list[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: f"EVT-{uuid4().hex[:12].upper()}")
    timestamp: str = field(default_factory=utc_timestamp)

    def __post_init__(self) -> None:
        object.__setattr__(self, "category", normalize_event_category(self.category))
        object.__setattr__(self, "severity", normalize_event_severity(self.severity))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize using stable string enum values."""
        data = asdict(self)
        data["category"] = self.category.value
        data["severity"] = self.severity.value
        return data

    def validate(self) -> None:
        """Raise ValueError when mandatory RULE-41 fields are absent."""
        data = self.to_dict()
        missing = [
            field_name
            for field_name in MANDATORY_EVENT_FIELDS
            if field_name not in data
        ]
        blank = [
            field_name
            for field_name in ("event_id", "trace_id", "timestamp", "module", "phase", "action")
            if not data.get(field_name)
        ]
        if missing or blank:
            raise ValueError(
                f"Invalid RULE-41 event. Missing={missing}; blank={blank}"
            )
