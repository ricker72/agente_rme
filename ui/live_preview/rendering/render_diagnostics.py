"""
Render diagnostics for WG-20U-A.
"""

from __future__ import annotations

from typing import Iterable

from .appearance_render_model import RenderedTile
from .appearance_tile_renderer import AppearanceTileRenderer


class RenderDiagnostics:
    """Computes renderer quality metrics."""

    def collect(
        self,
        tiles: Iterable[RenderedTile],
        renderer: AppearanceTileRenderer,
    ) -> dict[str, int]:
        tile_list = list(tiles)
        return {
            "renderable_appearances": sum(
                1 for tile in tile_list if tile.model.appearance_id
            ),
            "missing_appearances": sum(
                1 for tile in tile_list if not tile.model.appearance_id
            ),
            "fallback_render_count": sum(1 for tile in tile_list if tile.fallback_used),
            "invalid_role_mappings": sum(1 for tile in tile_list if tile.invalid),
            "tiles_rendered": renderer.tiles_rendered or len(tile_list),
            "floors_rendered": len({tile.floor for tile in tile_list}),
            "cache_hits": renderer.cache.stats.hits,
            "cache_misses": renderer.cache.stats.misses,
        }
