"""
Render layer manager for floor-aware WG-20U-A rendering.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List

from .appearance_render_model import RenderedTile


class RenderLayerManager:
    """Groups rendered tiles by floor."""

    def group_by_floor(self, tiles: Iterable[RenderedTile]) -> Dict[int, List[RenderedTile]]:
        grouped: Dict[int, List[RenderedTile]] = defaultdict(list)
        for tile in tiles:
            grouped[tile.floor].append(tile)
        return dict(grouped)

    def audit(self, tiles: Iterable[RenderedTile]) -> dict[str, object]:
        grouped = self.group_by_floor(tiles)
        return {
            "floor_aware_rendering": True,
            "floors_rendered": sorted(grouped),
            "tile_count": sum(len(values) for values in grouped.values()),
        }
