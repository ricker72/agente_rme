"""
Authoritative data adapter for WG-20U live preview widgets.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent


class LivePreviewDataProvider:
    """Loads WG-20TE and RULE-41 artifacts without recreating intelligence."""

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.workspace_root = Path(workspace_root or WORKSPACE_ROOT)
        self.bridge: Any = None
        self.datasets: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """Load all WG-20U authoritative data."""
        if self.bridge is None:
            from .wg20u_bridge import Wg20uStudioBridge

            self.bridge = Wg20uStudioBridge(self.workspace_root)
        result = self.bridge.load()
        self.datasets = self.bridge.validator._dataset_content  # noqa: SLF001
        return result

    @property
    def loaded(self) -> bool:
        return self.bridge is not None and bool(self.datasets)

    def viewport_data(self) -> Dict[str, Any]:
        return self.bridge.viewport_data()

    def connectivity_data(self) -> Dict[str, Any]:
        return self.bridge.connectivity_data()

    def critic_data(self) -> Dict[str, Any]:
        return self.bridge.critic_data()

    def playtest_data(self) -> Dict[str, Any]:
        return self.bridge.playtest_data()

    def tile_data(self, x: int, y: int, z: int) -> Dict[str, Any]:
        return self.bridge.tile_data(x, y, z)

    def event_stream(self) -> List[Dict[str, Any]]:
        stream = self.datasets.get("EVENT_STREAM.json", {})
        return stream.get("events", [])

    def trace_registry(self) -> Dict[str, Any]:
        return self.datasets.get("TRACE_REGISTRY.json", {})

    def timeline(self) -> List[Dict[str, Any]]:
        timeline = self.datasets.get("GENERATION_TIMELINE.json", {})
        return timeline.get("events", [])

    def observability_audit(self) -> Dict[str, Any]:
        return self.datasets.get("OBSERVABILITY_AUDIT.json", {})

    def appearance_sample(self, limit: int = 50) -> List[Dict[str, Any]]:
        path = self.workspace_root / "APPEARANCE_ITEM_CATALOG.json"
        if not path.exists():
            return []
        import json

        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            values = data.get("items") or data.get("appearances") or data.values()
        else:
            values = data
        rows = []
        for item in list(values)[:limit]:
            if isinstance(item, dict):
                rows.append(item)
        return rows

    def validation_report(self) -> Dict[str, Any]:
        return self.bridge.validator.validate_visual_truth()
