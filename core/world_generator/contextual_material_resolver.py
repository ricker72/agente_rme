from __future__ import annotations

import math
from collections import Counter
from typing import Any

from core.world_generator.semantic_color_blueprint import BlueprintLayer, SemanticColorBlueprint


class ContextualMaterialResolver:
    """Resolve semantic materials from spatial context before RME brush materialization."""

    def resolve(self, blueprint: SemanticColorBlueprint, plan: Any) -> dict[str, Any]:
        changes: Counter[str] = Counter()
        priority_profiles = getattr(plan, "architecture", {}).get("priority_style_profiles", {})
        terrain = blueprint.mask(BlueprintLayer.TERRAIN).cells
        for position, current in list(terrain.items()):
            region = _nearest_region(plan, position[0], position[1])
            desired = _terrain_for(
                region.style,
                region.terrain,
                current,
                position,
                priority_profiles.get(region.style, {}),
            )
            if desired != current:
                terrain[position] = desired
                changes[f"terrain:{current}->{desired}"] += 1

        for position, current in list(blueprint.mask(BlueprintLayer.ROAD).cells.items()):
            region = _nearest_region(plan, position[0], position[1])
            desired = _road_for(region.style, current)
            if desired != current:
                blueprint.mask(BlueprintLayer.ROAD).cells[position] = desired
                changes[f"road:{current}->{desired}"] += 1

        architecture = getattr(plan, "architecture", {})
        building_contexts = {
            tuple(building["center"]): building
            for settlement in architecture.get("settlements", ())
            for building in settlement.get("buildings", ())
        }
        for layer in (BlueprintLayer.STRUCTURE_GROUND, BlueprintLayer.WALL):
            for position, current in list(blueprint.mask(layer).cells.items()):
                building = _nearest_building(building_contexts, position)
                if building is None:
                    continue
                desired = _building_material(layer, building, current)
                if desired != current:
                    blueprint.mask(layer).cells[position] = desired
                    changes[f"{layer.name.lower()}:{current}->{desired}"] += 1

        for position, current in list(blueprint.mask(BlueprintLayer.NATURE).cells.items()):
            ground = terrain.get(position, "grass")
            desired = _nature_for(ground, position)
            if desired != current:
                blueprint.mask(BlueprintLayer.NATURE).cells[position] = desired
                changes[f"nature:{current}->{desired}"] += 1

        border = blueprint.mask(BlueprintLayer.TERRAIN_BORDER).cells
        for position, token in terrain.items():
            x, y, z = position
            neighbors = [terrain.get((x + dx, y + dy, z)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if any(neighbor != token for neighbor in neighbors):
                border[position] = "terrain_border"
        blueprint.metadata["contextual_material_resolution"] = {
            "status": "PASS",
            "changes": dict(sorted(changes.items())),
            "border_transition_tiles": len(border),
            "contexts": ["biome", "terrain", "neighbors", "interior", "exterior", "floor", "function"],
            "priority_profiles_used": sorted(priority_profiles),
            "certified_material_intents": len(
                getattr(plan, "reference_style", {}).get("semantic_ai", {}).get("material_intents", ())
            ),
            "material_authority": "certified palette + RME Brush Engine",
        }
        return blueprint.metadata["contextual_material_resolution"]


def _nearest_region(plan: Any, x: int, y: int) -> Any:
    containing = [region for region in plan.regions if region.contains(x, y)]
    if containing:
        # Hierarchical planner regions override their containing landmass.
        return min(containing, key=lambda region: region.radius[0] * region.radius[1])
    return min(plan.regions, key=lambda region: math.hypot(region.anchor[0] - x, region.anchor[1] - y))


def _terrain_for(
    style: str,
    terrain: str,
    current: str,
    position: tuple[int, int, int] | None = None,
    style_profile: dict[str, Any] | None = None,
) -> str:
    value = f"{style} {terrain}".lower()
    if current in {
        "krailos_dirt", "krailos_grass", "krailos_orange",
        "krailos_yellow", "krailos_purple", "rock_soil",
    }:
        return current
    if current == "grass" and "oasis" in value:
        return current
    if current == "mountain":
        return current
    if "dark" in value or "cavern" in value:
        return "mountain"
    if "dry" in value or "krailos" in value or "sand" in value or "ruin" in value:
        return "sand"
    if "swamp" in value or "wet" in value:
        if position is not None:
            x, y, z = position
            wetness = math.sin((x + z * 3) / 17.0) + math.cos((y - z * 2) / 21.0)
            reference_water = float((style_profile or {}).get("water_ratio", 0.0))
            threshold = max(0.45, min(0.9, 0.78 - reference_water * 0.8))
            return "swamp" if wetness > threshold else current
        return current
    return current


def _nature_for(ground: str, position: tuple[int, int, int]) -> str:
    x, y, z = position
    variant = abs(x * 73_856_093 ^ y * 19_349_663 ^ z * 83_492_791) % 10
    if ground == "swamp":
        return "swamp_tree" if variant < 4 else "swamp_plant"
    if ground == "sand":
        # Krailos is dry, but its readable nature grammar mixes rock details
        # with hardy shrubs instead of collapsing into one visual family.
        return "dry_rock_detail" if variant < 6 else "forest_shrub"
    if ground in {"krailos_dirt", "krailos_orange"}:
        return "krailos_rocks" if variant < 6 else "krailos_plant"
    if ground == "krailos_yellow":
        return "krailos_mountains" if variant < 3 else "krailos_rocks" if variant < 7 else "krailos_plant"
    if ground == "krailos_purple":
        return "krailos_rocks" if variant < 5 else "krailos_plant"
    if ground == "krailos_grass":
        return "krailos_plant" if variant < 7 else "krailos_rocks"
    if ground == "rock_soil":
        return "krailos_rocks" if variant < 8 else "dry_rock_detail"
    if ground == "mountain":
        return "dark_fungi" if variant < 6 else "dry_rock_detail"
    return "nature" if variant < 5 else "forest_shrub"


def _road_for(style: str, current: str) -> str:
    value = style.lower()
    if current == "rock_path":
        return current
    if "dark" in value or "cavern" in value:
        return "dark_path"
    if "dry" in value or "ruin" in value:
        return "dry_path"
    if "city" in value or "swamp" in value:
        return "city_road"
    return current


def _nearest_building(buildings: dict[tuple[int, int], dict[str, Any]], position: tuple[int, int, int]) -> dict[str, Any] | None:
    if not buildings:
        return None
    x, y, _ = position
    center, building = min(buildings.items(), key=lambda row: math.hypot(row[0][0] - x, row[0][1] - y))
    return building if abs(center[0] - x) <= building["width"] and abs(center[1] - y) <= building["height"] else None


def _building_material(layer: BlueprintLayer, building: dict[str, Any], current: str) -> str:
    if layer == BlueprintLayer.STRUCTURE_GROUND:
        return "civic_floor" if building["interior"] == "civic_stone" else "interior"
    if building["function"] in {"temple", "depot"}:
        return "ruin_wall"
    return current
