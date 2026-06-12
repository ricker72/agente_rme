from __future__ import annotations

from typing import Any, Dict


class StructureRenderer:
    def render_road_view(self, world_model: Any) -> Dict[str, object]:
        return {
            "roads": [road for road in getattr(world_model, "roads", [])],
            "paths": [
                road.get("path", []) for road in getattr(world_model, "roads", [])
            ],
        }

    def render_dungeon_view(self, world_model: Any) -> Dict[str, object]:
        return {
            "dungeons": [
                {
                    "name": dungeon.get("name"),
                    "theme": dungeon.get("theme"),
                    "floors": dungeon.get("floors"),
                    "difficulty": dungeon.get("difficulty"),
                    "connections": dungeon.get("connections", []),
                }
                for dungeon in getattr(world_model, "dungeons", [])
            ]
        }

    def render_city_view(self, world_model: Any) -> Dict[str, object]:
        return {
            "cities": [
                {
                    "name": city.get("name"),
                    "theme": city.get("theme"),
                    "population": city.get("population"),
                    "districts": city.get("districts", []),
                    "description": city.get("description", ""),
                }
                for city in getattr(world_model, "cities", [])
            ]
        }

    def render_biome_view(self, world_model: Any) -> Dict[str, object]:
        tiles = getattr(world_model, "tiles", {})
        biome_counts = {}
        for tile in tiles.values():
            ground = getattr(tile, "ground", "unknown")
            biome_counts[ground] = biome_counts.get(ground, 0) + 1
        return {
            "biome_distribution": biome_counts,
            "total_tiles": len(tiles),
        }
