from __future__ import annotations

from typing import Any, Dict, List, Optional


class TileRenderer:
    def render_tile(
        self, world_model: Any, x: int, y: int, z: int = 7
    ) -> Dict[str, object]:
        tile = getattr(world_model, "tiles", {}).get(f"{x}:{y}:{z}")
        if tile is None:
            return {"x": x, "y": y, "z": z, "exists": False}

        return {
            "x": tile.x,
            "y": tile.y,
            "z": tile.z,
            "ground": tile.ground,
            "items": getattr(tile, "items", []),
            "decorations": getattr(tile, "decorations", []),
            "spawn": getattr(tile, "spawn", None),
            "creature": getattr(tile, "creature", None),
            "exists": True,
        }

    def render_layer(self, world_model: Any, z: int = 7) -> List[Dict[str, object]]:
        return [
            {
                "x": tile.x,
                "y": tile.y,
                "ground": tile.ground,
                "spawn": getattr(tile, "spawn", None) is not None,
                "creature": getattr(tile, "creature", None) is not None,
            }
            for tile in getattr(world_model, "tiles", {}).values()
            if tile.z == z
        ]

    def render_area(
        self, world_model: Any, x: int, y: int, width: int, height: int, z: int = 7
    ) -> List[List[Optional[str]]]:
        tiles = getattr(world_model, "tiles", {})
        grid = []
        for row in range(y, y + height):
            line = []
            for col in range(x, x + width):
                tile = tiles.get(f"{col}:{row}:{z}")
                if tile is None:
                    line.append(None)
                else:
                    line.append(tile.ground)
            grid.append(line)
        return grid
