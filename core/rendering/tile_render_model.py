"""Tile render primitive for PMX-03 and later viewport work."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .appearance_models import ResolvedSprite


@dataclass(frozen=True)
class TileRenderModel:
    x: int
    y: int
    z: int
    ground_sprite: ResolvedSprite | None = None
    border_sprites: tuple[ResolvedSprite, ...] = ()
    item_sprites: tuple[ResolvedSprite, ...] = ()
    top_item_sprites: tuple[ResolvedSprite, ...] = ()
    selection_overlay: bool = False
    grid_overlay: bool = True
    brush_preview: ResolvedSprite | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
