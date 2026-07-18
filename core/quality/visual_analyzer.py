from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List


class VisualAnalyzer:
    def analyze(self, world_model: Any) -> Dict[str, object]:
        tiles = list(getattr(world_model, "tiles", {}).values())
        if not tiles:
            return {
                "tile_spam": False,
                "wall_spam": False,
                "empty_spaces": False,
                "overdecorated_zones": [],
                "dominant_ground_percentage": 0.0,
            }

        ground_counts = Counter(getattr(tile, "ground", "unknown") for tile in tiles)
        dominant_ground, dominant_count = ground_counts.most_common(1)[0]
        dominant_ratio = dominant_count / len(tiles)
        wall_count = sum(
            1
            for tile in tiles
            if "wall" in getattr(tile, "ground", "").lower()
            or any(
                "wall" in str(deco).lower() for deco in getattr(tile, "decorations", [])
            )
        )
        empty_ratio = self._compute_empty_space_ratio(tiles)
        overdecorated_zones = [
            {
                "x": tile.x,
                "y": tile.y,
                "z": tile.z,
                "decorations": len(getattr(tile, "decorations", [])),
            }
            for tile in tiles
            if len(getattr(tile, "decorations", [])) > 3
            or len(getattr(tile, "items", [])) > 4
        ]

        return {
            "tile_spam": dominant_ratio > 0.62,
            "wall_spam": wall_count / len(tiles) > 0.3,
            "empty_spaces": empty_ratio > 0.25,
            "overdecorated_zones": overdecorated_zones,
            "dominant_ground_percentage": round(dominant_ratio, 3),
            "wall_ratio": round(wall_count / len(tiles), 3),
            "empty_ratio": round(empty_ratio, 3),
        }

    def _compute_empty_space_ratio(self, tiles: List[Any]) -> float:
        xs = [tile.x for tile in tiles]
        ys = [tile.y for tile in tiles]
        zs = set(tile.z for tile in tiles)
        if not xs or not ys:
            return 1.0

        width = max(xs) - min(xs) + 1
        height = max(ys) - min(ys) + 1
        total_area = width * height * len(zs)
        return 1.0 - len(tiles) / max(total_area, 1)
