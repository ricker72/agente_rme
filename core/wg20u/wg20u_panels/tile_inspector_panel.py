"""
WG-20U Tile Inspector Panel - Consumes WG20TE_SEMANTIC_BRUSH_RESOLUTION_AUDIT.json,
WG20TE_ROLE_UNIQUENESS_AUDIT.json.

Displays:
    - Coordinates
    - Floor
    - Role
    - Selected Brush
    - Brush Family
    - Selection Reason
    - Semantic Validity
    - Collision Status
    - Source Module
    - Source Dataset
    - Trace ID
    - Parent Event
    - Validation Status
    - Generation Timestamp
    - Reasoning Chain
"""

from typing import Any, Dict, List, Optional


class TileInspectorPanel:
    """Tile inspector panel consuming WG-20TE brush resolution audit datasets."""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def inspect(
        self, datasets: Dict[str, Any], x: int, y: int, z: int
    ) -> Dict[str, Any]:
        """
        Inspect tile at coordinates using WG-20TE brush resolution data.

        Args:
            datasets: Loaded WG-20TE datasets
            x, y, z: Tile coordinates

        Returns:
            Dictionary with tile inspection data per WG-20TE audit
        """
        brush_audit = datasets.get(
            "WG20TE_SEMANTIC_BRUSH_RESOLUTION_AUDIT.json", {}
        )
        cache_key = f"{x}_{y}_{z}"

        # The brush resolution audit doesn't have per-tile coordinates,
        # but provides the authoritative brush mapping per role
        results = brush_audit.get("results", {})
        collisions = brush_audit.get("brush_collision_counts", {})
        collision_details = brush_audit.get("brush_collision_details", {})
        trace_events = datasets.get("LIVE_GENERATION_TRACE.jsonl", {}).get(
            "events", []
        )
        matching_event = self._find_tile_event(trace_events, x, y, z)

        # Find brushes by role for this tile context
        tile_data = {
            "coordinates": {"x": x, "y": y, "z": z},
            "floor": z,
            "roles_audited": brush_audit.get("roles_audited", []),
            "brush_mappings": results,
            "collision_status": self._check_collision_status(
                results, collisions, collision_details
            ),
            "semantic_valid": brush_audit.get("semantic_brush_audit_passed", False),
            "source_module": matching_event.get("module") if matching_event else None,
            "source_dataset": (
                matching_event.get("source_dataset") if matching_event else None
            ),
            "trace_id": matching_event.get("trace_id") if matching_event else None,
            "parent_event": (
                matching_event.get("parent_event") if matching_event else None
            ),
            "validation_status": (
                matching_event.get("result") if matching_event else "UNKNOWN"
            ),
            "generation_timestamp": (
                matching_event.get("timestamp") if matching_event else None
            ),
            "reasoning_chain": (
                matching_event.get("reasoning_chain", []) if matching_event else []
            ),
        }

        self._cache[cache_key] = tile_data
        return tile_data

    def _check_collision_status(
        self,
        results: Dict[str, Any],
        collisions: Dict[str, int],
        collision_details: Dict[str, List[str]],
    ) -> Dict[str, Any]:
        """Check collision status for brushes."""
        collision_entries = []
        for brush_name, collision_count in collisions.items():
            if collision_count > 1:
                collision_entries.append(
                    {
                        "brush": brush_name,
                        "colliding_roles": collision_details.get(brush_name, []),
                        "collision_count": collision_count,
                    }
                )

        return {
            "has_collisions": len(collision_entries) > 0,
            "collision_entries": collision_entries,
        }

    def _find_tile_event(
        self, events: List[Dict[str, Any]], x: int, y: int, z: int
    ) -> Optional[Dict[str, Any]]:
        """Find the authoritative RULE-41 event for a selected tile."""
        for event in reversed(events):
            coords = event.get("coordinates") or {}
            event_floor = event.get("floor", coords.get("z"))
            if coords.get("x") == x and coords.get("y") == y and event_floor == z:
                return event
        return None

    def get_cache(self) -> Dict[str, Dict[str, Any]]:
        """Return cached inspection results."""
        return self._cache.copy()

    def clear_cache(self) -> None:
        """Clear the inspection cache."""
        self._cache.clear()
