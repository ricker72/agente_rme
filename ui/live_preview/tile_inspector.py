"""
Tile inspector widget for WG-20U.
"""

from __future__ import annotations

from typing import Any, Dict

from .base_panel import TablePanel


class TileInspector(TablePanel):
    """Displays selected tile trace, brush, appearance, and validation data."""

    fields = [
        "Coordinates",
        "Floor",
        "Role",
        "Brush",
        "Brush Family",
        "Appearance ID",
        "Appearance Name",
        "Category",
        "Semantic Role",
        "Sprite IDs",
        "Animation Frames",
        "Atlas Reference",
        "Flags",
        "Source Module",
        "Source Dataset",
        "Trace ID",
        "Parent Event",
        "Validation Status",
        "Connectivity Status",
        "Reasoning Chain",
        "Render Status",
        "Fallback Used",
    ]

    def __init__(self) -> None:
        super().__init__("Tile Inspector", ["field", "value"])

    def set_tile(self, tile: Dict[str, Any]) -> None:
        coords = tile.get("coordinates", {})
        rows = [
            {"field": "Coordinates", "value": coords},
            {"field": "Floor", "value": tile.get("floor")},
            {"field": "Role", "value": tile.get("role")},
            {"field": "Brush", "value": tile.get("brush")},
            {"field": "Brush Family", "value": tile.get("brush_family")},
            {"field": "Appearance ID", "value": tile.get("appearance_id")},
            {"field": "Appearance Name", "value": tile.get("appearance_name")},
            {"field": "Category", "value": tile.get("category")},
            {"field": "Semantic Role", "value": tile.get("semantic_role")},
            {"field": "Sprite IDs", "value": tile.get("sprite_ids", [])},
            {"field": "Animation Frames", "value": tile.get("animation_frames")},
            {"field": "Atlas Reference", "value": tile.get("atlas_reference")},
            {"field": "Flags", "value": tile.get("flags", {})},
            {"field": "Source Module", "value": tile.get("source_module")},
            {"field": "Source Dataset", "value": tile.get("source_dataset")},
            {"field": "Trace ID", "value": tile.get("trace_id")},
            {"field": "Parent Event", "value": tile.get("parent_event")},
            {"field": "Validation Status", "value": tile.get("validation_status")},
            {"field": "Connectivity Status", "value": tile.get("connectivity_status", "UNKNOWN")},
            {"field": "Reasoning Chain", "value": tile.get("reasoning_chain", [])},
            {"field": "Render Status", "value": tile.get("render_status")},
            {"field": "Fallback Used", "value": tile.get("fallback_used", False)},
        ]
        self.set_rows(rows)
