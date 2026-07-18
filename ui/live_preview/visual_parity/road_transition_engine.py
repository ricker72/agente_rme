"""
Road transition engine for WG-20U-C.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from .common import VisualParityDatasetLoader, neighbor_list, normalize_role, same_family, trace_event


class RoadTransitionEngine:
    """Consumes road pattern rules to preview road continuity."""

    dataset_name = "RME_ROAD_PATTERN_RULES.json"

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.loader = VisualParityDatasetLoader(workspace_root)
        self.rules = self.loader.load(self.dataset_name)
        self.source_dataset = self.loader.resolved_sources.get(self.dataset_name, self.dataset_name)

    def preview(self, tile: Mapping[str, Any], neighbors: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
        connected = [
            entry["direction"]
            for entry in neighbor_list(neighbors)
            if normalize_role(entry["tile"]) == "ROAD" or same_family(tile, entry["tile"])
        ]
        return {
            "engine": "RoadTransitionEngine",
            "road_continuity": connected,
            "intersection_visualization": len(connected) >= 3,
            "corner_visualization": len(connected) == 2 and not (
                set(connected) in ({"north", "south"}, {"east", "west"})
            ),
            "trace": trace_event(
                tile,
                source_rule="road_pattern",
                source_dataset=self.source_dataset,
                reason="Resolved road continuity and intersections from certified road pattern rules.",
                correction="road_transition_preview",
                affected_tiles=[entry["tile"] for entry in neighbor_list(neighbors)],
            ),
        }

    def audit(self) -> Dict[str, Any]:
        return {
            "road_engine_ready": bool(self.rules),
            "dataset_requested": self.dataset_name,
            "source_dataset": self.source_dataset,
            "capabilities": ["road continuity", "intersection visualization", "corner visualization"],
        }
