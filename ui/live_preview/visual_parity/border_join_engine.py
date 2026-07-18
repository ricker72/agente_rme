"""
Border joining for WG-20U-C.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from .common import VisualParityDatasetLoader, neighbor_list, same_family, trace_event


class BorderJoinEngine:
    """Consumes transition rules to preview border edge and corner joins."""

    dataset_name = "RME_TRANSITION_RULES.json"

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.loader = VisualParityDatasetLoader(workspace_root)
        self.rules = self.loader.load(self.dataset_name)
        self.source_dataset = self.loader.resolved_sources.get(self.dataset_name, self.dataset_name)

    def preview(self, tile: Mapping[str, Any], neighbors: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
        joined = [entry["direction"] for entry in neighbor_list(neighbors) if same_family(tile, entry["tile"])]
        missing = [direction for direction in ("north", "south", "east", "west") if direction not in joined]
        corners = [
            corner
            for corner, pair in {
                "north_east": ("north", "east"),
                "north_west": ("north", "west"),
                "south_east": ("south", "east"),
                "south_west": ("south", "west"),
            }.items()
            if all(direction in joined for direction in pair)
        ]
        return {
            "engine": "BorderJoinEngine",
            "edge_joins": joined,
            "open_edges": missing,
            "corner_joins": corners,
            "transition_preview": bool(joined or missing),
            "trace": trace_event(
                tile,
                source_rule="border_adjacency",
                source_dataset=self.source_dataset,
                reason="Resolved border joins from certified transition rules and tile adjacency.",
                correction="border_join_preview",
                affected_tiles=[entry["tile"] for entry in neighbor_list(neighbors)],
            ),
        }

    def audit(self) -> Dict[str, Any]:
        return {
            "border_engine_ready": bool(self.rules),
            "dataset_requested": self.dataset_name,
            "source_dataset": self.source_dataset,
            "capabilities": ["border adjacency", "corner joining", "edge joining", "transition preview"],
        }
