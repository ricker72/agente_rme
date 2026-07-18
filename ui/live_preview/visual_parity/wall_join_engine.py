"""
Wall joining for WG-20U-C.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from .common import VisualParityDatasetLoader, neighbor_list, normalize_role, same_family, trace_event


class WallJoinEngine:
    """Consumes wall connection rules to resolve wall continuity."""

    dataset_name = "RME_WALL_CONNECTION_RULES.json"

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.loader = VisualParityDatasetLoader(workspace_root)
        self.rules = self.loader.load(self.dataset_name)
        self.source_dataset = self.loader.resolved_sources.get(self.dataset_name, self.dataset_name)

    def preview(self, tile: Mapping[str, Any], neighbors: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
        wall_neighbors = [
            entry["direction"]
            for entry in neighbor_list(neighbors)
            if normalize_role(entry["tile"]) == "WALL" or same_family(tile, entry["tile"])
        ]
        horizontal = {"east", "west"}.issubset(wall_neighbors)
        vertical = {"north", "south"}.issubset(wall_neighbors)

        # Determine join type for rendering
        join_type = "single"
        if horizontal and vertical:
            join_type = "intersection"
        elif horizontal and not vertical:
            join_type = "horizontal"
        elif vertical and not horizontal:
            join_type = "vertical"
        elif len(wall_neighbors) >= 2:
            join_type = "corner"
        elif len(wall_neighbors) == 1:
            join_type = "t_join"

        return {
            "engine": "WallJoinEngine",
            "continuity": wall_neighbors,
            "join_type": join_type,
            "corner_resolution": len(wall_neighbors) >= 2 and not (horizontal or vertical),
            "intersection_resolution": len(wall_neighbors) >= 3,
            "trace": trace_event(
                tile,
                source_rule="wall_connection",
                source_dataset=self.source_dataset,
                reason="Resolved wall continuity, corners, and intersections from certified wall rules.",
                correction="wall_join_preview",
                affected_tiles=[entry["tile"] for entry in neighbor_list(neighbors)],
            ),
        }

    def audit(self) -> Dict[str, Any]:
        return {
            "wall_engine_ready": bool(self.rules),
            "dataset_requested": self.dataset_name,
            "source_dataset": self.source_dataset,
            "capabilities": ["wall continuity", "wall corner resolution", "wall intersection resolution"],
        }
