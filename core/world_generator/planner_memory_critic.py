from __future__ import annotations

from typing import Any

from core.world_generator.semantic_color_blueprint import BlueprintLayer, SemanticColorBlueprint


class PlannerMemoryConformanceCritic:
    """Check an original blueprint against learned visual requirements, never source geometry."""

    def evaluate(self, blueprint: SemanticColorBlueprint, memory: dict[str, Any]) -> dict[str, Any]:
        terrain = set(blueprint.mask(BlueprintLayer.TERRAIN).cells)
        sea = set(blueprint.mask(BlueprintLayer.SEA_FOUNDATION).cells)
        nature = set(blueprint.mask(BlueprintLayer.NATURE).cells)
        walls = set(blueprint.mask(BlueprintLayer.WALL).cells)
        roofs = set(blueprint.mask(BlueprintLayer.ROOF).cells)
        structures = set(blueprint.mask(BlueprintLayer.STRUCTURE_GROUND).cells)
        floors = sorted({position[2] for position in blueprint.positions})
        effective_water = sea - terrain
        compact_scope = blueprint.metadata.get("plan_scale") == "compact"
        compact_nature = compact_scope and not walls and not structures
        checks = {
            # Corpus-wide priors describe large maps. They must not force an
            # unrelated upper floor or roof onto every compact single-floor task.
            "multifloor_present": compact_scope or not memory.get("requires_multifloor") or len(floors) >= 3,
            "roof_layer_present": compact_scope or not memory.get("requires_roofs") or bool(roofs),
            "wall_network_present": compact_nature or not memory.get("requires_wall_continuity") or len(walls) >= 4,
            "water_envelope_present": not memory.get("water_envelope_target") or bool(effective_water),
            "nature_clusters_present": not memory.get("nature_cluster_bias") or bool(nature),
        }
        metrics = {
            "designed_floors": floors,
            "roof_tiles": len(roofs),
            "wall_tiles": len(walls),
            "structure_tiles": len(structures),
            "effective_water_ratio": round(len(effective_water) / max(1, len(sea)), 6),
            "nature_per_terrain": round(len(nature) / max(1, len(terrain)), 6),
            "objective_scope": "compact_nature" if compact_nature else "compact_architecture" if compact_scope else "full",
        }
        return {
            "status": "PASS" if all(checks.values()) else "FAIL",
            "checks": checks,
            "metrics": metrics,
            "memory_reference_count": int(memory.get("reference_count", 0)),
            "policy": "require learned semantics while generating new coordinates and geometry",
        }
