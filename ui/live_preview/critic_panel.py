"""
WG-20U critic panel consuming RULE-41 issue events.
"""

from __future__ import annotations

from typing import Any, Dict

from .base_panel import TablePanel


class CriticPanel(TablePanel):
    """Displays disconnected roads, invalid floors, brush failures, and event issues."""

    def __init__(self) -> None:
        super().__init__("Critic", ["type", "severity", "message", "trace_id"])

    def set_data(self, data: Dict[str, Any]) -> None:
        rows = []
        for key in [
            "disconnected_roads",
            "invalid_floor_links",
            "invalid_brush_selections",
            "building_access_failures",
            "hunt_reachability_failures",
            "connectivity_warnings",
            "live_rule41_issues",
        ]:
            rows.extend(data.get(key, []))
        self.set_rows(rows)
