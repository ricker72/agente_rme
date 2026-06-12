"""
BlueprintFusionEngine — fuses two blueprints into a hybrid.

Supports:
  Roshamuul + Soul War
  Issavi + Falcon Bastion
  Library + Ferumbras
  Any combination with configurable ratio.
"""

from __future__ import annotations

import copy
import random
from typing import Any, Dict, List, Optional, Tuple

from core.blueprints.blueprint import Blueprint, BlueprintTile, BlueprintMetadata
from .models.blueprint_fusion import HybridBlueprint
from .blueprint_embedding_engine import BlueprintEmbeddingEngine


class BlueprintFusionEngine:
    """
    Fuses two blueprints into a hybrid blueprint.
    """

    def __init__(
        self,
        embedding_engine: Optional[BlueprintEmbeddingEngine] = None,
    ) -> None:
        self.embedding_engine = embedding_engine or BlueprintEmbeddingEngine()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fuse(
        self,
        blueprint_a: Blueprint,
        blueprint_b: Blueprint,
        ratio: float = 0.5,
        method: str = "weighted",
        name: Optional[str] = None,
    ) -> HybridBlueprint:
        """
        Fuse two blueprints into a hybrid.

        Args:
            blueprint_a: First source blueprint.
            blueprint_b: Second source blueprint.
            ratio: Weight of blueprint_a (0.0 = all b, 1.0 = all a).
            method: Fusion method ('weighted', 'interleave', 'blend').
            name: Optional name for the hybrid.

        Returns:
            HybridBlueprint containing the fused result.
        """
        ratio = max(0.0, min(1.0, ratio))

        if method == "interleave":
            hybrid_bp = self._fuse_interleave(blueprint_a, blueprint_b, ratio)
        elif method == "blend":
            hybrid_bp = self._fuse_blend(blueprint_a, blueprint_b, ratio)
        else:
            hybrid_bp = self._fuse_weighted(blueprint_a, blueprint_b, ratio)

        hybrid_name = name or f"{blueprint_a.name}_x_{blueprint_b.name}_r{ratio:.1f}"

        return HybridBlueprint(
            name=hybrid_name,
            blueprint=hybrid_bp,
            source_a=blueprint_a.name,
            source_b=blueprint_b.name,
            fusion_ratio=ratio,
            fusion_method=method,
            critic_score=0.0,
            playtest_score=0.0,
        )

    # ------------------------------------------------------------------
    # Fusion Methods
    # ------------------------------------------------------------------

    @staticmethod
    def _fuse_weighted(a: Blueprint, b: Blueprint, ratio: float) -> Blueprint:
        """Weighted fusion: blend tiles proportionally."""
        name = f"{a.name}_x_{b.name}"
        size = (
            max(a.size[0], b.size[0]),
            max(a.size[1], b.size[1]),
        )

        result = Blueprint(
            name=name,
            category="hybrid",
            theme=f"{a.theme}_{b.theme}",
            size=size,
            metadata=BlueprintMetadata(
                style=f"{a.metadata.style}_{b.metadata.style}",
                tags=a.metadata.tags + b.metadata.tags,
                hybrid=True,
            ),
        )

        # Merge tiles
        all_tiles: Dict[Tuple[int, int], BlueprintTile] = {}
        for tile in a.tiles:
            all_tiles[(tile.x, tile.y)] = copy.deepcopy(tile)

        for tile in b.tiles:
            key = (tile.x, tile.y)
            if key in all_tiles:
                if random.random() > ratio:
                    all_tiles[key] = copy.deepcopy(tile)
            else:
                all_tiles[key] = copy.deepcopy(tile)

        result.tiles = list(all_tiles.values())

        # Merge descriptive data
        result.rooms = _merge_list(a.rooms, b.rooms, ratio)
        result.features = _merge_list(a.features, b.features, ratio)
        result.zones = _merge_list(a.zones, b.zones, ratio)
        result.grounds = _merge_list(a.grounds, b.grounds, ratio)

        return result

    @staticmethod
    def _fuse_interleave(a: Blueprint, b: Blueprint, ratio: float) -> Blueprint:
        """Interleave: alternate rows/columns from each source."""
        result = Blueprint(
            name=f"{a.name}_x_{b.name}_interleave",
            category="hybrid",
            theme=f"{a.theme}_{b.theme}",
            size=(max(a.size[0], b.size[0]), max(a.size[1], b.size[1])),
            metadata=BlueprintMetadata(
                style=f"{a.metadata.style}_{b.metadata.style}",
                tags=a.metadata.tags + b.metadata.tags,
                hybrid=True,
            ),
        )

        all_tiles: Dict[Tuple[int, int], BlueprintTile] = {}
        tile_map_a = {(t.x, t.y): t for t in a.tiles}
        tile_map_b = {(t.x, t.y): t for t in b.tiles}

        (
            max(
                max((t.x for t in a.tiles), default=0),
                max((t.x for t in b.tiles), default=0),
            )
            + 1
        )

        for y in range(result.size[1]):
            use_a = y % 2 == 0
            tiles_source = tile_map_a if use_a else tile_map_b
            for x in range(result.size[0]):
                key = (x, y)
                if key in tiles_source:
                    all_tiles[key] = copy.deepcopy(tiles_source[key])

        result.tiles = list(all_tiles.values())
        result.rooms = _interleave_list(a.rooms, b.rooms)
        result.features = _interleave_list(a.features, b.features)
        return result

    @staticmethod
    def _fuse_blend(a: Blueprint, b: Blueprint, ratio: float) -> Blueprint:
        """Blend: mix features at the tile level with randomness."""
        result = Blueprint(
            name=f"{a.name}_x_{b.name}_blend",
            category="hybrid",
            theme=f"{a.theme}_{b.theme}",
            size=(max(a.size[0], b.size[0]), max(a.size[1], b.size[1])),
            metadata=BlueprintMetadata(
                style=f"{a.metadata.style}_{b.metadata.style}",
                tags=a.metadata.tags + b.metadata.tags,
                hybrid=True,
            ),
        )

        all_tiles: Dict[Tuple[int, int], BlueprintTile] = {}
        tile_map_a = {(t.x, t.y): t for t in a.tiles}
        tile_map_b = {(t.x, t.y): t for t in b.tiles}

        for key, tile_a in tile_map_a.items():
            if key in tile_map_b:
                tile_b = tile_map_b[key]
                blended = copy.deepcopy(tile_a)
                if tile_b.ground and random.random() > ratio:
                    blended.ground = tile_b.ground
                if tile_b.item and random.random() > ratio:
                    blended.item = tile_b.item
                if tile_b.decoration and random.random() > ratio:
                    blended.decoration = tile_b.decoration
                if tile_b.spawn and random.random() > ratio:
                    blended.spawn = tile_b.spawn
                all_tiles[key] = blended
            else:
                if random.random() < ratio:
                    all_tiles[key] = copy.deepcopy(tile_a)

        for key, tile_b in tile_map_b.items():
            if key not in all_tiles and random.random() < (1.0 - ratio):
                all_tiles[key] = copy.deepcopy(tile_b)

        result.tiles = list(all_tiles.values())
        return result


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


def _merge_list(list_a: List[Any], list_b: List[Any], ratio: float) -> List[Any]:
    """Merge two lists by taking ratio from a, (1-ratio) from b."""
    count_a = int(len(list_a) * ratio)
    count_b = int(len(list_b) * (1.0 - ratio))
    merged = list(list_a[:count_a]) + list(list_b[:count_b])
    random.shuffle(merged)
    return merged


def _interleave_list(list_a: List[Any], list_b: List[Any]) -> List[Any]:
    """Interleave two lists."""
    result: List[Any] = []
    max_len = max(len(list_a), len(list_b))
    for i in range(max_len):
        if i < len(list_a):
            result.append(list_a[i])
        if i < len(list_b):
            result.append(list_b[i])
    return result
