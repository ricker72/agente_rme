"""
Preview Report — genera preview.json con estadísticas del mapa.

Salida:
{
  "tiles": 1250,
  "grounds": 1100,
  "items": 80,
  "spawns": 25,
  "bosses": 1,
  "structures": 5
}
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List

from . import palette


def generate_report(world_model: Any) -> Dict[str, Any]:
    """
    Genera un reporte JSON-serializable con estadísticas del WorldModel.

    Args:
        world_model: Instancia de WorldModel.

    Returns:
        Dict con tiles, grounds, items, spawns, bosses, structures.
    """
    tiles = getattr(world_model, "tiles", {})
    structures = getattr(world_model, "structures", [])
    regions = getattr(world_model, "regions", [])

    total_tiles = len(tiles)
    total_grounds = 0
    total_walls = 0
    total_items = 0
    total_spawns = 0
    total_bosses = 0
    total_decorations = 0

    ground_ids: set = set()
    boss_details: List[Dict[str, Any]] = []
    spawn_details: List[Dict[str, Any]] = []
    z_layers: Dict[int, int] = defaultdict(int)

    for tile in tiles.values():
        tz = getattr(tile, "z", None)
        if tz is not None:
            z_layers[tz] += 1

        # Ground
        ground = getattr(tile, "ground", None)
        if ground is not None:
            ground_ids.add(ground)
            if ground in palette.WALL_IDS:
                total_walls += 1
            else:
                total_grounds += 1

        # Items
        items = getattr(tile, "items", [])
        if items:
            total_items += len(items)
            for item in items:
                item_id = getattr(item, "itemid", None)
                if item_id is None:
                    item_id = item.get("id") if isinstance(item, dict) else None
                if item_id is not None and item_id in palette.DECORATION_IDS:
                    total_decorations += 1

        # Spawns / Bosses
        spawn = getattr(tile, "spawn", None)
        if spawn is not None:
            monster = getattr(spawn, "monster", "")
            detail = {
                "x": getattr(tile, "x", 0),
                "y": getattr(tile, "y", 0),
                "z": getattr(tile, "z", 7),
                "monster": monster,
                "respawn": getattr(spawn, "respawn", 60),
                "radius": getattr(spawn, "radius", 5),
            }
            if monster and palette.is_boss(monster):
                total_bosses += 1
                boss_details.append(detail)
            else:
                total_spawns += 1
                spawn_details.append(detail)

    # Reporte estructurado
    report = {
        "tiles": total_tiles,
        "grounds": total_grounds,
        "walls": total_walls,
        "items": total_items,
        "decorations": total_decorations,
        "spawns": total_spawns,
        "bosses": total_bosses,
        "structures": len(structures),
        "regions": len(regions),
        "z_layers": dict(sorted(z_layers.items())),
        "unique_ground_ids": len(ground_ids),
        "summary": (
            f"{total_tiles} tiles | "
            f"{total_grounds + total_walls} grounds ({total_walls} walls) | "
            f"{total_items} items ({total_decorations} deco) | "
            f"{total_spawns + total_bosses} spawns ({total_bosses} bosses) | "
            f"{len(structures)} structures"
        ),
    }

    # Detalles opcionales (limitados para no explotar el JSON)
    report["spawn_details"] = spawn_details[:50]
    report["boss_details"] = boss_details[:10]

    return report
