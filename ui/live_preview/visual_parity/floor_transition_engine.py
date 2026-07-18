"""
Floor transition engine for WG-20U-C.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from .common import trace_event


class FloorTransitionEngine:
    """Consumes WG20TE floor graph for stairs, ramps, teleports, and links."""

    dataset_name = "WG20TE_FLOOR_GRAPH.json"

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.workspace_root = Path(workspace_root or Path.cwd())
        self.rules = self._load()

    def preview(self, tile: Mapping[str, Any]) -> Dict[str, Any]:
        role = str(tile.get("role") or tile.get("semantic_role") or "").upper()
        connectors = self.rules.get("connector_types_supported", []) if isinstance(self.rules, dict) else []
        connector = next((item for item in connectors if item.rstrip("s").upper() in role), "")
        return {
            "engine": "FloorTransitionEngine",
            "stairs_preview": connector == "stairs",
            "ramp_preview": connector == "ramps",
            "teleport_preview": connector == "teleports",
            "floor_link_visualization": bool(connector),
            "connector": connector,
            "trace": trace_event(
                tile,
                source_rule="floor_graph_edge",
                source_dataset=self.dataset_name,
                reason="Resolved floor link visualization from consumed WG20TE floor graph.",
                correction="floor_transition_preview",
            ),
        }

    def audit(self) -> Dict[str, Any]:
        return {
            "floor_transition_ready": bool(self.rules),
            "dataset_requested": self.dataset_name,
            "source_dataset": self.dataset_name if (self.workspace_root / self.dataset_name).exists() else "",
            "capabilities": ["stairs preview", "ramp preview", "teleport preview", "floor link visualization"],
        }

    def _load(self) -> Dict[str, Any]:
        path = self.workspace_root / self.dataset_name
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
