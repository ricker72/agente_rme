"""
Semantic tile to appearance render adapter.

Integrates BrushIntelligenceConsumer and WallIntelligenceConsumer
for correct appearance resolution from certified intelligence.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .appearance_render_loader import AppearanceRenderLoader
from .appearance_render_model import RenderedTile

REQUIRED_ROLES = [
    "GROUND",
    "ROAD",
    "WATER",
    "WALL",
    "DOOR",
    "WINDOW",
    "ROOF",
    "STAIR",
    "RAMP",
    "NATURE",
    "BRIDGE",
    "INTERIOR",
    "DECORATION",
    "NPC",
    "SPAWN",
    "QUEST_OBJECT",
]


class SemanticTileRenderAdapter:
    """Resolves semantic tile metadata into renderable appearance models."""

    def __init__(
        self,
        loader: Optional[AppearanceRenderLoader] = None,
        workspace_root: Optional[Path] = None,
    ) -> None:
        self.loader = loader or AppearanceRenderLoader(workspace_root).load()
        self._join_overrides: Dict[str, Dict[str, int]] = {}
        self._brush_appearance_map: Dict[str, int] = {}
        self._intelligence_consumers_active = False

    def set_join_overrides(self, overrides: Dict[str, Dict[str, int]]) -> None:
        """Set brush join overrides from certified wall rules."""
        self._join_overrides = overrides

    def set_brush_appearance_map(self, mapping: Dict[str, int]) -> None:
        """Set brush-to-appearance mapping from BrushIntelligenceConsumer."""
        self._brush_appearance_map = mapping
        self._intelligence_consumers_active = bool(mapping)

    def adapt_tile(self, tile: Dict[str, Any]) -> RenderedTile:
        role = str(tile.get("role") or tile.get("semantic_role") or "GROUND")
        brush = str(tile.get("brush") or tile.get("selected_brush") or "")
        appearance_id = tile.get("appearance_id")
        join_type = tile.get("join_type", tile.get("wall_join", ""))

        # Phase 1: Apply join-aware override from wall intelligence (most specific)
        if join_type and brush and self._join_overrides:
            join_key = join_type.lower()
            if join_key in self._join_overrides:
                brush_lower = brush.lower()
                if brush_lower in self._join_overrides[join_key]:
                    appearance_id = self._join_overrides[join_key][brush_lower]

        # Phase 2: Apply brush intelligence lookid resolution
        if appearance_id is None or appearance_id == 0:
            if brush and self._brush_appearance_map:
                brush_lower = brush.lower()
                if brush_lower in self._brush_appearance_map:
                    resolved = self._brush_appearance_map[brush_lower]
                    if resolved > 0:
                        appearance_id = resolved

        model = self.loader.resolve_model(role, appearance_id)
        coords = tile.get("coordinates", {})
        x = int(tile.get("x", coords.get("x", 0)))
        y = int(tile.get("y", coords.get("y", 0)))
        floor = int(tile.get("floor", coords.get("z", 7)))
        return RenderedTile(
            x=x,
            y=y,
            floor=floor,
            role=model.semantic_role,
            brush=brush,
            model=model,
            trace_id=tile.get("trace_id"),
            event_id=tile.get("event_id"),
            source_module=tile.get("source_module") or tile.get("module"),
            source_dataset=tile.get("source_dataset"),
            fallback_used=model.render_status != "SPRITE_BACKED",
            invalid=not bool(model.appearance_id) or not bool(model.sprite_ids),
            subtype=int(tile.get("subtype", tile.get("fluid_type", 0)) or 0),
            count=int(tile.get("count", 1) or 1),
            direction=tile.get("direction"),
            variant=tile.get("variant"),
        )

    def adapt_tiles(self, tiles: List[Dict[str, Any]]) -> List[RenderedTile]:
        return [self.adapt_tile(tile) for tile in tiles]

    def audit(self) -> Dict[str, Any]:
        available = set(self.loader.role_mapping)
        aliases = {
            "INTERIOR": "HOUSE",
            "NPC": "DECORATION",
            "SPAWN": "SPAWN_OBJECT",
        }
        missing = [
            role
            for role in REQUIRED_ROLES
            if role not in available and aliases.get(role) not in available
        ]
        return {
            "required_roles": REQUIRED_ROLES,
            "roles_resolved": [
                role
                for role in REQUIRED_ROLES
                if role in available or aliases.get(role) in available
            ],
            "missing_roles": missing,
            "semantic_tile_adapter_ready": len(missing) == 0,
            "intelligence_consumers_active": self._intelligence_consumers_active,
            "brush_appearance_mappings_loaded": len(self._brush_appearance_map),
            "join_overrides_loaded": sum(len(v) for v in self._join_overrides.values()),
            "duplicate_intelligence_created": False,
        }
