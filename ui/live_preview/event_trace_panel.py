"""
RULE-41 event trace table.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .base_panel import TablePanel


class EventTracePanel(TablePanel):
    """Displays EVENT_STREAM and TRACE_REGISTRY fields."""

    def __init__(self) -> None:
        super().__init__(
            "Event Trace",
            [
                "event_id",
                "trace_id",
                "module",
                "timestamp",
                "severity",
                "action",
                "coordinates",
                "result",
                "duration_ms",
                "parent_event",
            ],
        )

    def set_events(self, events: List[Dict[str, Any]]) -> None:
        self.set_rows(events)
