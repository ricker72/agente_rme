from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core.world_generator.rme_brush_engine import RMEBrushEngine


@dataclass(frozen=True)
class WallVariantFootprint:
    item_id: int
    variant: str
    width_tiles: int
    height_tiles: int
    pattern_width: int
    pattern_height: int

    @property
    def extends_anchor(self) -> bool:
        return self.width_tiles > 1 or self.height_tiles > 1


@dataclass(frozen=True)
class WallFamilyFootprint:
    brush_name: str
    variants: tuple[WallVariantFootprint, ...]
    max_width_tiles: int
    max_height_tiles: int
    max_pattern_span: int
    logical_occupancy_tiles: int = 1
    placement_rule: str = "one logical wall per map tile; sprite overlap is resolved by RME draw order"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class WallBrushVisualFootprintModel:
    """Joins RME WallBrush variants with official appearance sprite dimensions."""

    def __init__(self, render_catalog: dict[str, dict[str, Any]]) -> None:
        self.render_catalog = render_catalog

    @classmethod
    def load(cls, root: str | Path = ".") -> "WallBrushVisualFootprintModel":
        path = Path(root) / "APPEARANCE_RENDER_CATALOG.json"
        payload = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        return cls(payload)

    def profile(self, engine: RMEBrushEngine, brush_name: str) -> WallFamilyFootprint:
        brush = engine.wall_brush(brush_name)
        if brush is None:
            raise KeyError(f"Unknown WallBrush: {brush_name}")
        variants = tuple(
            self._variant(item.item_id, variant)
            for variant, items in sorted(brush.variants.items())
            for item in items
        )
        return WallFamilyFootprint(
            brush_name=brush.name,
            variants=variants,
            max_width_tiles=max((value.width_tiles for value in variants), default=1),
            max_height_tiles=max((value.height_tiles for value in variants), default=1),
            max_pattern_span=max(
                (max(value.pattern_width, value.pattern_height) for value in variants),
                default=1,
            ),
        )

    def audit(self, engine: RMEBrushEngine, brush_names: set[str]) -> dict[str, Any]:
        families = [self.profile(engine, name).to_dict() for name in sorted(brush_names)]
        return {
            "status": "PASS" if len(families) == len(brush_names) else "FAIL",
            "source": "APPEARANCE_RENDER_CATALOG.json derived from official appearances.dat",
            "family_count": len(families),
            "families": families,
        }

    def _variant(self, item_id: int, variant: str) -> WallVariantFootprint:
        render = self.render_catalog.get(str(item_id), {})
        return WallVariantFootprint(
            item_id=item_id,
            variant=variant,
            width_tiles=max(1, int(render.get("width", 1) or 1)),
            height_tiles=max(1, int(render.get("height", 1) or 1)),
            pattern_width=max(1, int(render.get("pattern_width", 1) or 1)),
            pattern_height=max(1, int(render.get("pattern_height", 1) or 1)),
        )
