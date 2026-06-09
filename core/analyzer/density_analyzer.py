"""
HITO 12 — Density Analyzer: analiza densidad de tiles, items, spawns
y población en el mapa.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any, Dict, List


class DensityAnalyzer:
    """Analiza densidades de tiles, items, spawns en el mapa."""

    def analyze(
        self,
        tiles: Dict[str, int],
        items: Dict[str, int],
        spawns: List[Dict[str, object]],
        map_size: Dict[str, int],
    ) -> Dict[str, object]:
        """Analiza densidades del mapa.

        Args:
            tiles: Dict {tile_type: count}.
            items: Dict {item_type: count}.
            spawns: Lista de spawns.
            map_size: Dict {"width": w, "height": h} del mapa.

        Returns:
            Dict con métricas de densidad.
        """
        width = map_size.get("width", 1)
        height = map_size.get("height", 1)
        area = max(width * height, 1)

        total_tiles = sum(tiles.values())
        total_items = sum(items.values())
        total_spawns = len(spawns)

        # Densidad por tipo de tile
        tile_density = self._compute_tile_density(tiles, area)

        # Densidad de items
        item_density = self._compute_item_density(items, total_tiles)

        # Densidad de spawns
        spawn_density = self._compute_spawn_density(spawns, area, width, height)

        # Heatmap por cuadrantes
        heatmap = self._compute_spawn_heatmap(spawns, width, height)

        # Distribución por floors
        floor_dist = self._compute_floor_distribution(spawns)

        # Score de densidad general
        density_score = self._compute_overall_density(
            total_tiles, total_items, total_spawns, area
        )

        return {
            "map_area": area,
            "total_tiles": total_tiles,
            "total_items": total_items,
            "total_spawns": total_spawns,
            "tile_density": tile_density,
            "item_density": item_density,
            "spawn_density": spawn_density,
            "overall_density_score": density_score,
            "density_category": self._categorize_density(density_score),
            "spawn_heatmap": heatmap,
            "floor_distribution": floor_dist,
            "items_per_tile": round(total_items / max(total_tiles, 1), 3),
            "spawns_per_tile": round(total_spawns / max(total_tiles, 1), 5),
        }

    # ------------------------------------------------------------------
    # Densidad de tiles
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_tile_density(tiles: Dict[str, int], area: int) -> Dict[str, object]:
        """Calcula densidad de tiles por tipo y global."""
        if not tiles:
            return {"total_density": 0.0, "top_types": []}

        total = sum(tiles.values())
        density = round(total / max(area, 1), 4)

        top = sorted(tiles.items(), key=lambda x: x[1], reverse=True)[:10]
        top_with_pct = [
            {"type": t, "count": c, "percentage": round(100 * c / max(total, 1), 2)}
            for t, c in top
        ]

        return {
            "total_density": density,
            "top_types": top_with_pct,
            "unique_tile_types": len(tiles),
        }

    @staticmethod
    def _compute_item_density(
        items: Dict[str, int], total_tiles: int
    ) -> Dict[str, object]:
        """Calcula densidad de items respecto a tiles."""
        if not items:
            return {"items_per_tile": 0.0, "top_items": []}

        total_items = sum(items.values())
        items_per_tile = round(total_items / max(total_tiles, 1), 3)

        top = sorted(items.items(), key=lambda x: x[1], reverse=True)[:10]
        top_with_pct = [
            {"item": i, "count": c, "percentage": round(100 * c / max(total_items, 1), 2)}
            for i, c in top
        ]

        return {
            "items_per_tile": items_per_tile,
            "total_items": total_items,
            "unique_item_types": len(items),
            "top_items": top_with_pct,
        }

    # ------------------------------------------------------------------
    # Densidad de spawns
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_spawn_density(
        spawns: List[Dict[str, object]],
        area: int,
        width: int,
        height: int,
    ) -> Dict[str, object]:
        """Calcula densidad de spawns en el mapa."""
        if not spawns:
            return {
                "spawns_per_sq": 0.0,
                "spawns_per_100sq": 0.0,
                "concentration_zone": "none",
            }

        spawns_per_sq = round(len(spawns) / max(area, 1), 6)
        spawns_per_100sq = round(len(spawns) * 10000 / max(area, 1), 2)

        # Zona de concentración
        if spawns:
            avg_x = sum(int(sp.get("x", 0)) for sp in spawns) / len(spawns)
            avg_y = sum(int(sp.get("y", 0)) for sp in spawns) / len(spawns)
            quadrant = _get_quadrant(avg_x, avg_y, width, height)
        else:
            quadrant = "none"

        # Monstruos únicos
        unique = len(set(sp.get("monster", "unknown") for sp in spawns))

        return {
            "spawns_per_sq": spawns_per_sq,
            "spawns_per_100sq": spawns_per_100sq,
            "unique_monsters": unique,
            "concentration_center": {"x": round(avg_x) if spawns else 0, "y": round(avg_y) if spawns else 0},
            "concentration_zone": quadrant,
        }

    # ------------------------------------------------------------------
    # Heatmap
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_spawn_heatmap(
        spawns: List[Dict[str, object]],
        width: int,
        height: int,
        grid_size: int = 50,
    ) -> List[Dict[str, object]]:
        """Genera heatmap de spawns por celdas."""
        if not spawns or width <= 0 or height <= 0:
            return []

        cols = max(1, width // grid_size)
        rows = max(1, height // grid_size)
        grid = defaultdict(int)

        for sp in spawns:
            x = int(sp.get("x", 0))
            y = int(sp.get("y", 0))
            col = x // grid_size
            row = y // grid_size
            grid[(col, row)] += 1

        cells = []
        for (col, row), count in grid.items():
            cells.append({
                "col": col,
                "row": row,
                "x1": col * grid_size,
                "y1": row * grid_size,
                "x2": min((col + 1) * grid_size - 1, width - 1),
                "y2": min((row + 1) * grid_size - 1, height - 1),
                "spawn_count": count,
                "density": round(count / (grid_size * grid_size), 4),
            })

        cells.sort(key=lambda c: c["spawn_count"], reverse=True)
        return cells[:25]

    # ------------------------------------------------------------------
    # Floor distribution
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_floor_distribution(
        spawns: List[Dict[str, object]],
    ) -> Dict[str, object]:
        """Distribución de spawns por floor."""
        if not spawns:
            return {"by_floor": {}}

        floor_counts = Counter()
        for sp in spawns:
            z = int(sp.get("z", 0))
            floor_counts[z] += 1

        return {
            "by_floor": {str(k): v for k, v in sorted(floor_counts.items())},
            "dominant_floor": max(floor_counts, key=floor_counts.get) if floor_counts else 0,
        }

    # ------------------------------------------------------------------
    # Overall density score
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_overall_density(
        total_tiles: int,
        total_items: int,
        total_spawns: int,
        area: int,
    ) -> float:
        """Calcula score de densidad general (0-100)."""
        if area <= 0:
            return 0.0

        tile_score = min(total_tiles / max(area, 1), 1.0) * 40
        item_score = min(total_items / max(total_tiles, 1), 1.0) * 30
        spawn_score = min(total_spawns / max(area / 100, 1), 1.0) * 30

        return round(tile_score + item_score + spawn_score, 2)

    @staticmethod
    def _categorize_density(score: float) -> str:
        """Categoriza la densidad según score."""
        if score >= 80:
            return "very_high"
        if score >= 60:
            return "high"
        if score >= 40:
            return "medium"
        if score >= 20:
            return "low"
        return "very_low"


def _get_quadrant(x: float, y: float, width: int, height: int) -> str:
    """Determina el cuadrante de un punto."""
    mid_x = width / 2
    mid_y = height / 2

    if x < mid_x:
        return "NW" if y < mid_y else "SW"
    else:
        return "NE" if y < mid_y else "SE"