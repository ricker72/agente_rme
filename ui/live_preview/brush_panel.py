"""
Brush intelligence panel.
"""

from __future__ import annotations

from typing import Any, Dict

from .base_panel import TablePanel


class BrushPanel(TablePanel):
    """Consumes WG20TE_SEMANTIC_BRUSH_RESOLUTION_AUDIT.json."""

    def __init__(self) -> None:
        super().__init__("Brushes", ["role", "brush", "family", "usage_count", "validation_status"])

    def set_audit(self, audit: Dict[str, Any]) -> None:
        rows = []
        collisions = audit.get("brush_collision_counts", {})
        for role, data in audit.get("results", {}).items():
            brush = data.get("selected_brush", data.get("brush", ""))
            rows.append(
                {
                    "role": role,
                    "brush": brush,
                    "family": data.get("family", data.get("brush_family", "")),
                    "usage_count": collisions.get(brush, 1),
                    "validation_status": data.get("semantic_valid", True),
                }
            )
        self.set_rows(rows)
