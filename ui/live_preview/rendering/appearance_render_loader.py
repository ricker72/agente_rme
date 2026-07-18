"""
Load authoritative appearance render catalogs for WG-20U-A.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from core.opentibia.assets.appearance_dat_flags import AppearanceDatFlagExtractor

from .appearance_render_model import AppearanceRenderModel


ROLE_COLORS = {
    "GROUND": "#6B5B3E",
    "ROAD": "#8A7450",
    "WATER": "#236B8E",
    "WALL": "#58515C",
    "DOOR": "#7A5436",
    "WINDOW": "#8BA9C9",
    "ROOF": "#7C3838",
    "STAIR": "#A58B5F",
    "RAMP": "#9E835C",
    "NATURE": "#2F704F",
    "BRIDGE": "#806746",
    "INTERIOR": "#725F4A",
    "DECORATION": "#917A48",
    "NPC": "#48A0A8",
    "SPAWN": "#9B4B4B",
    "QUEST_OBJECT": "#8D5FBF",
}


class AppearanceRenderLoader:
    """Consumes APPEARANCE_* catalogs without recreating them."""

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.workspace_root = Path(workspace_root or Path.cwd())
        self.render_catalog: Dict[str, Dict[str, Any]] = {}
        self.item_catalog: Dict[str, Dict[str, Any]] = {}
        self.role_mapping: Dict[str, list[int]] = {}
        self.flag_extractor: AppearanceDatFlagExtractor | None = None

    def load(self) -> "AppearanceRenderLoader":
        self.render_catalog = self._load_json("APPEARANCE_RENDER_CATALOG.json")
        self.item_catalog = self._load_json("APPEARANCE_ITEM_CATALOG.json")
        self.role_mapping = self._load_json("APPEARANCE_RME_ROLE_MAPPING.json")
        appearances_path = self._resolve_appearances_dat()
        if appearances_path is not None and appearances_path.exists():
            self.flag_extractor = AppearanceDatFlagExtractor(appearances_path)
        return self

    def audit(self) -> Dict[str, Any]:
        return {
            "render_catalog_loaded": bool(self.render_catalog),
            "item_catalog_loaded": bool(self.item_catalog),
            "role_mapping_loaded": bool(self.role_mapping),
            "render_catalog_count": len(self.render_catalog),
            "item_catalog_count": len(self.item_catalog),
            "role_mapping_count": len(self.role_mapping),
            "appearance_dat_flags": self.flag_extractor.audit() if self.flag_extractor else {
                "appearance_dat_flag_extractor_ready": False,
            },
            "duplicate_intelligence_created": False,
        }

    def resolve_model(
        self,
        role: str,
        appearance_id: Optional[int] = None,
    ) -> AppearanceRenderModel:
        role_key = self._normalize_role(role)
        resolved_id = appearance_id or self._first_role_appearance(role_key)
        render = self.render_catalog.get(str(resolved_id), {})
        item = self.item_catalog.get(str(resolved_id), {})
        exact_sprite = (
            self.flag_extractor.extract_sprite_info_from_catalog_entry(int(resolved_id or 0), render)
            if self.flag_extractor and render
            else None
        )
        sprite_ids = list(exact_sprite.sprite_ids) if exact_sprite and exact_sprite.sprite_ids else [
            int(sprite) for sprite in render.get("sprite_ids", [])
        ]
        sprite_backed = bool(render) and bool(sprite_ids)
        exact_flags = self._exact_dat_flags(int(resolved_id or 0), render)
        flags = dict(item.get("server_attributes", {}) or {})
        flags.update(exact_flags.flags)
        flags.update(self._flag_aliases(exact_flags.flags))
        dimensions = {
            "width": int(render.get("width", 1) or 1),
            "height": int(render.get("height", 1) or 1),
            "pattern_width": int(render.get("pattern_width", 1) or 1),
            "pattern_height": int(render.get("pattern_height", 1) or 1),
            "pattern_depth": exact_sprite.pattern_depth if exact_sprite else int(
                render.get("pattern_depth", 1) or 1
            ),
        }
        return AppearanceRenderModel(
            appearance_id=int(resolved_id or 0),
            name=str(item.get("name") or render.get("name") or f"appearance {resolved_id}"),
            category=str(item.get("server_type") or role_key.lower()),
            semantic_role=role_key,
            sprite_ids=sprite_ids,
            dimensions=dimensions,
            layers=exact_sprite.layers if exact_sprite else int(render.get("layers", 1) or 1),
            animation_frames=exact_sprite.animation.frame_count if exact_sprite else int(
                render.get("animation_frames", 1) or 1
            ),
            flags=flags,
            render_metadata={
                "catalog_offset": render.get("offset"),
                "message_size": render.get("message_size"),
                "pattern_width": exact_sprite.pattern_width if exact_sprite else render.get("pattern_width", 1),
                "pattern_height": exact_sprite.pattern_height if exact_sprite else render.get("pattern_height", 1),
                "pattern_depth": exact_sprite.pattern_depth if exact_sprite else render.get("pattern_depth", 1),
                "sprite_count": render.get("sprite_count", len(sprite_ids)),
                "metadata": render.get("metadata", {}),
                "exact_appearance_dat_flags": exact_flags.to_dict(),
                "sprite_animation": exact_sprite.animation.to_dict() if exact_sprite else {},
                "exact_sprite_info": exact_sprite.to_dict() if exact_sprite else {},
            },
            fallback_color=ROLE_COLORS.get(role_key, "#1D2330"),
            render_status="SPRITE_BACKED" if sprite_backed else "MISSING_SPRITE",
        )

    def _first_role_appearance(self, role: str) -> int:
        ids = self.role_mapping.get(role) or self.role_mapping.get(role.upper()) or []
        for appearance_id in ids:
            if str(appearance_id) in self.render_catalog:
                return int(appearance_id)
        return int(ids[0]) if ids else 0

    def _normalize_role(self, role: str) -> str:
        role_key = str(role or "GROUND").upper()
        aliases = {
            "SPAWN_OBJECT": "SPAWN",
            "SPAWN": "SPAWN_OBJECT",
            "TEMPLE": "DECORATION",
            "DEPOT": "DECORATION",
            "SHOP": "INTERIOR",
            "INTERIOR": "HOUSE",
            "NPC": "DECORATION",
        }
        return aliases.get(role_key, role_key)

    def _load_json(self, name: str) -> Any:
        path = self.workspace_root / name
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _exact_dat_flags(self, appearance_id: int, render: dict[str, Any]) -> Any:
        if self.flag_extractor is None or not render:
            from core.opentibia.assets.appearance_dat_flags import AppearanceDatFlags

            return AppearanceDatFlags(appearance_id)
        return self.flag_extractor.extract_from_catalog_entry(appearance_id, render)

    def _flag_aliases(self, flags: dict[str, Any]) -> dict[str, Any]:
        aliases: dict[str, Any] = {}
        if "unpass" in flags:
            aliases["unpassable"] = flags["unpass"]
            aliases["blocksolid"] = flags["unpass"]
        if "unsight" in flags:
            aliases["block_missiles"] = flags["unsight"]
        if "avoid" in flags:
            aliases["block_pathfinder"] = flags["avoid"]
        if "take" in flags:
            aliases["pickupable"] = flags["take"]
        if "unmove" in flags:
            aliases["moveable"] = not bool(flags["unmove"])
        if "draw_offset_x" in flags or "draw_offset_y" in flags:
            aliases["shift_x"] = int(flags.get("draw_offset_x", 0) or 0)
            aliases["shift_y"] = int(flags.get("draw_offset_y", 0) or 0)
        if "elevation" in flags:
            aliases["draw_height"] = flags["elevation"]
        return aliases

    def _resolve_appearances_dat(self) -> Path | None:
        catalog = self.workspace_root / "assets" / "catalog-content.json"
        if not catalog.exists():
            return None
        try:
            data = json.loads(catalog.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        if not isinstance(data, list):
            return None
        for entry in data:
            if isinstance(entry, dict) and entry.get("type") == "appearances":
                return catalog.parent / str(entry.get("file", ""))
        return None
