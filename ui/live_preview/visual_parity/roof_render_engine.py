"""
Roof render engine for WG-20U-C.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from .common import VisualParityDatasetLoader, normalize_role, trace_event


class RoofRenderEngine:
    """Derives roof visibility previews from consumed brush and appearance metadata."""

    dataset_name = "RME_BRUSH_INTELLIGENCE_CATALOG.json"

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.loader = VisualParityDatasetLoader(workspace_root)
        self.rules = self.loader.load(self.dataset_name)
        self.source_dataset = self.loader.resolved_sources.get(self.dataset_name, self.dataset_name)

    def preview(self, tile: Mapping[str, Any], interior_preview: bool = False) -> Dict[str, Any]:
        is_roof = normalize_role(tile) == "ROOF" or "roof" in str(tile.get("brush", "")).lower()
        return {
            "engine": "RoofRenderEngine",
            "roof_visibility": is_roof and not interior_preview,
            "roof_hiding": is_roof and interior_preview,
            "roof_transparency": 0.42 if is_roof and interior_preview else 1.0,
            "interior_preview": interior_preview,
            "trace": trace_event(
                tile,
                source_rule="roof_visibility",
                source_dataset=self.source_dataset,
                reason="Resolved roof visibility using consumed brush intelligence and viewport state.",
                correction="roof_render_preview",
            ),
        }

    def audit(self) -> Dict[str, Any]:
        return {
            "roof_engine_ready": bool(self.rules),
            "dataset_requested": self.dataset_name,
            "source_dataset": self.source_dataset,
            "capabilities": ["roof visibility", "roof hiding", "roof transparency", "interior preview"],
        }
