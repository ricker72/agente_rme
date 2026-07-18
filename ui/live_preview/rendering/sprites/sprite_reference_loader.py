"""
Sprite reference extraction from authoritative appearance catalogs.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

from core.opentibia.assets.appearance_dat_flags import (
    AppearanceDatFlagExtractor,
    SpriteAnimationInfo,
)


@dataclass(frozen=True)
class SpriteReference:
    """Sprite metadata extracted for one appearance."""

    appearance_id: int
    sprite_ids: list[int] = field(default_factory=list)
    frame_count: int = 1
    layers: int = 1
    patterns: dict[str, int] = field(default_factory=dict)
    dimensions: dict[str, int] = field(default_factory=dict)
    animation: SpriteAnimationInfo = field(default_factory=SpriteAnimationInfo)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SpriteReferenceLoader:
    """Consumes existing catalogs to expose appearance sprite references."""

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.workspace_root = Path(workspace_root or Path.cwd())
        self.render_catalog: dict[str, dict[str, Any]] = {}
        self.item_catalog: dict[str, dict[str, Any]] = {}
        self.dat_extractor: AppearanceDatFlagExtractor | None = None

    def load(self) -> "SpriteReferenceLoader":
        self.render_catalog = self._load_json("APPEARANCE_RENDER_CATALOG.json")
        self.item_catalog = self._load_json("APPEARANCE_ITEM_CATALOG.json")
        appearances = sorted((self.workspace_root / "assets").glob("appearances-*.dat"))
        if appearances:
            self.dat_extractor = AppearanceDatFlagExtractor(appearances[0])
        return self

    def iter_references(self, limit: int | None = None) -> Iterable[SpriteReference]:
        count = 0
        for key in sorted(self.render_catalog, key=lambda value: int(value)):
            yield self.resolve(int(key))
            count += 1
            if limit is not None and count >= limit:
                return

    def resolve(self, appearance_id: int) -> SpriteReference:
        render = self.render_catalog.get(str(int(appearance_id)), {})
        exact = (
            self.dat_extractor.extract_sprite_info_from_catalog_entry(appearance_id, render)
            if self.dat_extractor and render
            else None
        )
        sprite_ids = list(exact.sprite_ids) if exact and exact.sprite_ids else [
            int(sprite) for sprite in render.get("sprite_ids", [])
        ]
        frame_count = exact.animation.frame_count if exact else int(
            render.get("animation_frames", 1) or 1
        )
        layers = exact.layers if exact else int(render.get("layers", 1) or 1)
        patterns = {
            "width": exact.pattern_width if exact else int(render.get("pattern_width", 1) or 1),
            "height": exact.pattern_height if exact else int(render.get("pattern_height", 1) or 1),
            "depth": exact.pattern_depth if exact else int(render.get("pattern_depth", 1) or 1),
        }
        dimensions = {
            "width": int(render.get("width", 1) or 1),
            "height": int(render.get("height", 1) or 1),
        }
        return SpriteReference(
            appearance_id=int(appearance_id),
            sprite_ids=sprite_ids,
            frame_count=max(1, frame_count),
            layers=max(1, layers),
            patterns=patterns,
            dimensions=dimensions,
            animation=exact.animation if exact else SpriteAnimationInfo(),
        )

    def audit(self) -> dict[str, Any]:
        references = list(self.iter_references())
        with_sprites = [ref for ref in references if ref.sprite_ids]
        unique_sprite_ids = {sprite for ref in with_sprites for sprite in ref.sprite_ids}
        return {
            "sprite_reference_extraction_ready": bool(with_sprites),
            "appearances_checked": len(references),
            "appearances_with_sprites": len(with_sprites),
            "appearances_without_sprites": len(references) - len(with_sprites),
            "unique_sprite_ids": len(unique_sprite_ids),
            "source_dataset": "APPEARANCE_RENDER_CATALOG.json",
            "exact_appearances_dat_sprite_info": self.dat_extractor is not None,
            "duplicate_intelligence_created": False,
        }

    def _load_json(self, name: str) -> Any:
        path = self.workspace_root / name
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
