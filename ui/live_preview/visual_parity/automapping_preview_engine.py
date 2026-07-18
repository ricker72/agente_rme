"""
Automapping preview engine for WG-20U-C.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

from .common import VisualParityDatasetLoader, normalize_brush, trace_event


class AutomappingPreviewEngine:
    """Consumes automapping rules to preview affected tiles and applied rules."""

    dataset_name = "RME_AUTOMAPPING_RULES.json"

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.loader = VisualParityDatasetLoader(workspace_root)
        self.rules = self.loader.load(self.dataset_name)
        self.source_dataset = self.loader.resolved_sources.get(self.dataset_name, self.dataset_name)

    def preview(self, tile: Mapping[str, Any], affected_tiles: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
        brush = normalize_brush(tile)
        dependencies = self.rules.get("automapping_dependencies", {}) if isinstance(self.rules, dict) else {}
        applied = dependencies.get(brush, [])
        affected = list(affected_tiles)
        return {
            "engine": "AutomappingPreviewEngine",
            "automapping_preview": True,
            "applied_rules": applied,
            "affected_tile_count": len(affected),
            "trace": trace_event(
                tile,
                source_rule="automapping_dependency",
                source_dataset=self.source_dataset,
                reason="Previewed automapping result using consumed automapping dependencies.",
                correction="automapping_preview",
                affected_tiles=affected,
            ),
        }

    def audit(self) -> Dict[str, Any]:
        return {
            "automapping_ready": bool(self.rules),
            "dataset_requested": self.dataset_name,
            "source_dataset": self.source_dataset,
            "capabilities": ["preview automapping result", "show applied rules", "show affected tiles"],
        }
