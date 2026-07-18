from __future__ import annotations

from typing import Any, Dict, Mapping


def evaluate_population_constraints(models: Mapping[str, Any]) -> Dict[str, Any]:
    invalid_npc_regions = [npc["id"] for npc in models["npcs"]["npcs"] if not npc.get("settlement_id")]
    impossible_habitats = [eco["id"] for eco in models["ecosystems"]["ecosystems"] if not eco.get("official_reference_names")]
    conflicting_factions = _duplicates(faction["id"] for faction in models["factions"]["factions"])
    excessive_density = len(models["npcs"]["npcs"]) > max(1, len(models["services"]["services"]) * 2)
    invalid_overlap = []
    return {
        "artifact": "POPULATION_CONSTRAINTS",
        "logical_only": True,
        "invalid_ecosystem_overlap": invalid_overlap,
        "invalid_npc_regions": invalid_npc_regions,
        "impossible_habitats": impossible_habitats,
        "conflicting_factions": conflicting_factions,
        "excessive_density": excessive_density,
        "valid": not invalid_overlap and not invalid_npc_regions and not impossible_habitats and not conflicting_factions and not excessive_density,
    }


def _duplicates(values) -> list[str]:
    seen = set()
    dupes = set()
    for value in values:
        if value in seen:
            dupes.add(value)
        seen.add(value)
    return sorted(dupes)
