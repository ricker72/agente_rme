from __future__ import annotations

from typing import Any, Dict, Mapping

BIOME_CREATURE_REFERENCES = {
    "arid": ("scarab", "nomad", "lion"),
    "polar": ("frost_troll", "winter_wolf", "ice_golem"),
    "temperate": ("wolf", "bear", "rotworm"),
}


def plan_ecosystems(inputs: Mapping[str, Any]) -> Dict[str, Any]:
    blueprint = inputs["CERTIFIED_BLUEPRINT.json"]
    ecosystems = []
    for region in sorted(blueprint.get("regions", []), key=lambda item: item["id"]):
        climate = str(region.get("climate") or "temperate")
        creatures = BIOME_CREATURE_REFERENCES.get(climate, BIOME_CREATURE_REFERENCES["temperate"])
        ecosystems.append(
            {
                "id": f"ecosystem_{region['id']}",
                "region_id": region["id"],
                "biome_affinity": climate,
                "habitat_suitability": "certified_metadata",
                "ecological_density": _density(climate),
                "food_chain_classification": ["prey", "predator", "apex_anchor"],
                "danger_level": _danger(climate),
                "official_reference_names": list(creatures),
                "monsters_written_to_otbm": False,
            }
        )
    return {"artifact": "MONSTER_ECOSYSTEM_MODEL", "logical_only": True, "ecosystems": ecosystems}


def _density(climate: str) -> str:
    return {"arid": "medium", "polar": "low", "temperate": "high"}.get(climate, "medium")


def _danger(climate: str) -> str:
    return {"arid": "medium", "polar": "high", "temperate": "low"}.get(climate, "medium")
