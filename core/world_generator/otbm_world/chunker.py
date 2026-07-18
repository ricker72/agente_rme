from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple

from .model import OtbmTile, OtbmWorldModel

AREA_SIZE = 256


@dataclass(frozen=True)
class TileArea:
    base_x: int
    base_y: int
    z: int
    tiles: Tuple[OtbmTile, ...]

    def to_json_dict(self) -> dict:
        return asdict(self)


def chunk_tile_areas(world: OtbmWorldModel) -> Tuple[TileArea, ...]:
    grouped: Dict[Tuple[int, int, int], List[OtbmTile]] = {}
    for tile in world.tiles:
        base_x = (tile.x // AREA_SIZE) * AREA_SIZE
        base_y = (tile.y // AREA_SIZE) * AREA_SIZE
        grouped.setdefault((tile.z, base_x, base_y), []).append(tile)

    areas: List[TileArea] = []
    for z, base_x, base_y in sorted(grouped):
        tiles = tuple(sorted(grouped[(z, base_x, base_y)], key=lambda tile: (tile.x, tile.y, tile.z)))
        areas.append(TileArea(base_x=base_x, base_y=base_y, z=z, tiles=tiles))
    return tuple(areas)
