"""
WG-20U: Visual Validator for connectivity intelligence.

Consumes WG-20TE authoritative datasets to provide visual validation
of floor connectivity, building accessibility, hunt reachability, and
semantic brush resolution.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from .wg20u_loader import Wg20uDatasetLoader
from .wg20u_viewport import Wg20uViewport
from .wg20u_panels import (
    ConnectivityPanel,
    TileInspectorPanel,
    CriticPanel,
    PlaytestPanel,
    FloorGraphOverlay,
)
from .wg20u_validator import Wg20uValidator

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent


class Wg20uVisualValidator:
    """
    Main entry point for WG-20U validation.

    Loads WG-20TE datasets and provides visual panels for:
    - Viewport: Floor graph, stair links, ramp links, building/hunt accessibility,
                path continuity, brush resolution, role resolution
    - Connectivity Panel: Floor nodes, edges, connector types, orphan connectors
    - Tile Inspector: Coordinates, role, brush selection, collision status
    - Critic Panel: Disconnected roads, invalid floor links, building access failures
    - Playtest Panel: Accessible buildings, reachable hunts/floors, navigation validation
    - Floor Graph Overlay: Floor nodes, edges, connector visualization
    """

    REQUIRED_DATASETS = [
        "WG20TE_SEMANTIC_BRUSH_RESOLUTION_AUDIT.json",
        "WG20TE_ROLE_UNIQUENESS_AUDIT.json",
        "WG20TE_FLOOR_GRAPH.json",
        "WG20TE_STAIR_CONNECTIVITY.json",
        "WG20TE_RAMP_CONNECTIVITY.json",
        "WG20TE_BUILDING_ACCESS_VALIDATION.json",
        "WG20TE_HUNT_REACHABILITY.json",
        "WG20TE_PATH_CONTINUITY.json",
        "WG20TE_VALIDATION.json",
        "WG20TE_QUALITY_REPORT.json",
        "WG20TE_BRIDGE_CONNECTIVITY.json",
    ]
    RULE41_DATASETS = [
        "LIVE_GENERATION_TRACE.jsonl",
        "EVENT_STREAM.json",
        "TRACE_REGISTRY.json",
        "GENERATION_TIMELINE.json",
        "OBSERVABILITY_AUDIT.json",
    ]

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or WORKSPACE_ROOT
        self.loader = Wg20uDatasetLoader(self.workspace_root)
        self.viewport = Wg20uViewport()
        self.connectivity_panel = ConnectivityPanel()
        self.tile_inspector = TileInspectorPanel()
        self.critic_panel = CriticPanel()
        self.playtest_panel = PlaytestPanel()
        self.floor_graph_overlay = FloorGraphOverlay()
        self.validator = Wg20uValidator()

        self._datasets_loaded = False
        self._dataset_content: Dict[str, Any] = {}

    def load_datasets(self) -> Dict[str, Any]:
        """Load all required WG-20TE datasets. Returns certification status."""
        missing = []
        for dataset_name in self.REQUIRED_DATASETS:
            path = self.workspace_root / dataset_name
            if path.exists():
                self._dataset_content[dataset_name] = self.loader.load_dataset(dataset_name)
            else:
                missing.append(dataset_name)

        self._datasets_loaded = len(missing) == 0

        if missing:
            return {
                "certification_status": "WG20TE_DATASET_CONSUMPTION_MISSING",
                "missing_datasets": missing,
                "blockers": ["RME_LIKE_LIVE_PREVIEW_BLOCKED"],
                "valid": False,
            }

        self._dataset_content.update(self.loader.load_rule41_trace_artifacts())

        return {
            "certification_status": "PASS",
            "loaded_datasets": list(self._dataset_content.keys()),
            "valid": True,
        }

    def validate_visual_truth(self) -> Dict[str, Any]:
        """
        Validate that rendered world agrees with WG-20TE data.

        Returns VISUAL_TRUTH_FAILED if any discrepancy found.
        """
        if not self._datasets_loaded:
            return self.load_datasets()

        return self.validator.validate_all(self._dataset_content)

    def get_viewport_data(self) -> Dict[str, Any]:
        """Get viewport visualization data from all datasets."""
        return self.viewport.render(self._dataset_content)

    def get_connectivity_panel_data(self) -> Dict[str, Any]:
        """Get connectivity panel data (floor nodes, edges, connectors)."""
        return self.connectivity_panel.render(self._dataset_content)

    def get_tile_inspector_data(self, x: int, y: int, z: int) -> Dict[str, Any]:
        """Get tile inspector data for coordinates (x, y, z)."""
        return self.tile_inspector.inspect(self._dataset_content, x, y, z)

    def get_critic_panel_data(self) -> Dict[str, Any]:
        """Get critic panel validation issues."""
        return self.critic_panel.render(self._dataset_content)

    def get_playtest_panel_data(self) -> Dict[str, Any]:
        """Get playtest panel navigation validation data."""
        return self.playtest_panel.render(self._dataset_content)

    def get_floor_graph_overlay_data(self) -> Dict[str, Any]:
        """Get floor graph overlay visualization data."""
        return self.floor_graph_overlay.render(self._dataset_content)

    def get_all_panel_data(self) -> Dict[str, Any]:
        """Get aggregated data for all panels."""
        return {
            "viewport": self.get_viewport_data(),
            "connectivity_panel": self.get_connectivity_panel_data(),
            "tile_inspector": self.tile_inspector.get_cache(),
            "critic_panel": self.get_critic_panel_data(),
            "playtest_panel": self.get_playtest_panel_data(),
            "floor_graph_overlay": self.get_floor_graph_overlay_data(),
            "live_generation_trace_panel": self.get_viewport_data().get(
                "live_generation_trace_panel", {}
            ),
            "wg20te_validation": self._dataset_content.get(
                "WG20TE_VALIDATION.json", {}
            ),
            "wg20te_quality_report": self._dataset_content.get(
                "WG20TE_QUALITY_REPORT.json", {}
            ),
        }


__all__ = [
    "Wg20uVisualValidator",
    "Wg20uDatasetLoader",
    "Wg20uViewport",
    "Wg20uValidator",
    "ConnectivityPanel",
    "TileInspectorPanel",
    "CriticPanel",
    "PlaytestPanel",
    "FloorGraphOverlay",
]
