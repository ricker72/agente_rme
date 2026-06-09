from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Tuple


class HeatmapRenderer:
    def render_spawn_heatmap(self, world_model: Any) -> Dict[str, object]:
        return self._render_heatmap(world_model, mode="spawn")

    def render_difficulty_heatmap(self, world_model: Any) -> Dict[str, object]:
        return self._render_heatmap(world_model, mode="difficulty")

    def _render_heatmap(self, world_model: Any, mode: str) -> Dict[str, object]:
        tiles = getattr(world_model, "tiles", {})
        if not tiles:
            return {"grid": [], "legend": {}, "mode": mode}

        intensity = defaultdict(int)
        bounds = self._compute_bounds(tiles)

        if mode == "spawn":
            for spawn in getattr(world_model, "spawns", []):
                zone = spawn.get("zone")
                coords = self._zone_center(spawn)
                if coords:
                    intensity[coords] += 3
        else:
            for boss in getattr(world_model, "bosses", []) + getattr(world_model, "dungeons", []):
                coords = self._zone_center(boss)
                if coords:
                    intensity[coords] += 4 if boss.get("difficulty") in ("hard", "deadly", "legendary") else 2

        grid = self._build_grid(bounds, intensity)
        return {
            "mode": mode,
            "grid": grid,
            "x_offset": bounds[2],
            "y_offset": bounds[3],
            "legend": {
                "0": "none",
                "1": "low",
                "2": "medium",
                "3": "high",
                "4": "peak",
            },
        }

    def _compute_bounds(self, tiles: Dict[str, Any]) -> Tuple[int, int, int, int]:
        xs = [tile.x for tile in tiles.values()]
        ys = [tile.y for tile in tiles.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        return max_x - min_x + 1, max_y - min_y + 1, min_x, min_y

    def _zone_center(self, zone: Dict[str, object]) -> Tuple[int, int]:
        x = zone.get("x")
        y = zone.get("y")
        width = zone.get("width", 1)
        height = zone.get("height", 1)
        if x is None or y is None:
            return None
        return (x + width // 2, y + height // 2)

    def _build_grid(self, bounds: Tuple[int, int, int, int], intensity: Dict[Tuple[int, int], int]) -> List[List[int]]:
        width, height, min_x, min_y = bounds
        grid = [[0 for _ in range(width)] for _ in range(height)]
        for (x, y), value in intensity.items():
            if min_x <= x < min_x + width and min_y <= y < min_y + height:
                grid[y - min_y][x - min_x] = min(value, 4)
        return grid
