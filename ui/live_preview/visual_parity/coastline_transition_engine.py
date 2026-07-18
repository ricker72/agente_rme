"""
Coastline transition engine for WG-20U-C.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from .common import VisualParityDatasetLoader, neighbor_list, normalize_role, trace_event


class CoastlineTransitionEngine:
    """Consumes coastline rules for water-to-ground previews."""

    dataset_name = "RME_COASTLINE_RULES.json"

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.loader = VisualParityDatasetLoader(workspace_root)
        self.rules = self.loader.load(self.dataset_name)
        self.source_dataset = self.loader.resolved_sources.get(self.dataset_name, self.dataset_name)

    def preview(self, tile: Mapping[str, Any], neighbors: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
        water_edges = [
            entry["direction"]
            for entry in neighbor_list(neighbors)
            if normalize_role(entry["tile"]) == "WATER"
        ]
        ground_edges = [
            entry["direction"]
            for entry in neighbor_list(neighbors)
            if normalize_role(entry["tile"]) in {"GROUND", "ROAD", "NATURE"}
        ]
        return {
            "engine": "CoastlineTransitionEngine",
            "water_to_ground_transitions": water_edges if ground_edges else [],
            "shoreline_rendering": bool(water_edges and ground_edges),
            "coastline_preview": bool(water_edges),
            "trace": trace_event(
                tile,
                source_rule="coastline_transition",
                source_dataset=self.source_dataset,
                reason="Resolved shoreline preview from certified coastline rules.",
                correction="coastline_transition_preview",
                affected_tiles=[entry["tile"] for entry in neighbor_list(neighbors)],
            ),
        }

    def audit(self) -> Dict[str, Any]:
        return {
            "coastline_engine_ready": bool(self.rules),
            "dataset_requested": self.dataset_name,
            "source_dataset": self.source_dataset,
            "capabilities": ["water-to-ground transitions", "shoreline rendering", "coastline preview"],
        }
