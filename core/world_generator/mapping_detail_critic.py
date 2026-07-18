from __future__ import annotations

from collections import Counter

from core.world_generator.semantic_color_blueprint import BlueprintLayer, SemanticColorBlueprint


class MappingDetailCritic:
    """Block monoculture, unsupported roofs and visibly broken specialist walls."""

    def evaluate(self, blueprint: SemanticColorBlueprint) -> dict[str, object]:
        nature = Counter(blueprint.mask(BlueprintLayer.NATURE).cells.values())
        terrain = Counter(blueprint.mask(BlueprintLayer.TERRAIN).cells.values())
        walls = blueprint.mask(BlueprintLayer.WALL).cells
        rosh = {position for position, token in walls.items() if token == "roshamuul_wall"}
        isolated = sum(_neighbor_count(position, rosh) == 0 for position in rosh)
        endpoints = sum(_neighbor_count(position, rosh) == 1 for position in rosh)
        roofs = set(blueprint.mask(BlueprintLayer.ROOF).cells)
        structure = set(blueprint.mask(BlueprintLayer.STRUCTURE_GROUND).cells)
        supported = sum((x, y, z + 1) in structure for x, y, z in roofs)
        roof_support_ratio = supported / len(roofs) if roofs else 1.0
        nature_total = sum(nature.values())
        nature_max_share = max(nature.values(), default=0) / nature_total if nature_total else 1.0
        compact = blueprint.metadata.get("plan_scale") == "compact"
        nature_family_minimum = 3 if compact else 5
        terrain_family_minimum = 2 if compact else 4
        checks = {
            "nature_family_count": len(nature) >= nature_family_minimum if nature_total >= 100 else True,
            "nature_not_monoculture": nature_max_share <= 0.65,
            "terrain_family_count": len(terrain) >= terrain_family_minimum if sum(terrain.values()) >= 1000 else True,
            "roshamuul_no_isolated_walls": isolated == 0,
            "roshamuul_endpoint_ratio": endpoints / len(rosh) <= 0.18 if rosh else True,
            "roof_support_ratio": roof_support_ratio >= 0.90,
        }
        return {
            "status": "PASS" if all(checks.values()) else "BLOCKED",
            "checks": checks,
            "metrics": {
                "nature_tokens": dict(sorted(nature.items())),
                "nature_max_share": round(nature_max_share, 6),
                "terrain_tokens": dict(sorted(terrain.items())),
                "roshamuul_wall_tiles": len(rosh),
                "roshamuul_isolated_tiles": isolated,
                "roshamuul_endpoints": endpoints,
                "roof_tiles": len(roofs),
                "roof_support_ratio": round(roof_support_ratio, 6),
                "plan_scale": "compact" if compact else "full",
            },
        }


def _neighbor_count(position: tuple[int, int, int], positions: set[tuple[int, int, int]]) -> int:
    x, y, z = position
    return sum((x + dx, y + dy, z) in positions for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
