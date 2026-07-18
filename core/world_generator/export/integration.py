from __future__ import annotations

from typing import Any, Dict, Mapping


def build_integration_model(inputs: Mapping[str, Any], otbm_hash: str) -> Dict[str, Any]:
    gameplay = inputs["CERTIFIED_GAMEPLAY_METADATA.json"]
    population = inputs["CERTIFIED_POPULATION_MODEL.json"]
    return {
        "artifact": "WORLD_EXPORT_MODEL",
        "integration_only": True,
        "deployment_ready": True,
        "otbm_fingerprint": otbm_hash,
        "certified_sources": {
            "blueprint": inputs["CERTIFIED_BLUEPRINT.json"].get("metadata", {}).get("world_id"),
            "otbm_world": inputs["CERTIFIED_OTBM_WORLD.json"].get("fingerprint"),
            "gameplay": gameplay.get("fingerprint"),
            "population": population.get("fingerprint"),
        },
        "counts": {
            "towns": len(gameplay.get("models", {}).get("towns", {}).get("towns", [])),
            "houses": len(gameplay.get("models", {}).get("houses", {}).get("houses", [])),
            "waypoints": len(gameplay.get("models", {}).get("waypoints", {}).get("nodes", [])),
            "spawn_distributions": len(population.get("models", {}).get("spawns", {}).get("distributions", [])),
            "npc_metadata": len(population.get("models", {}).get("npcs", {}).get("npcs", [])),
        },
        "compatibility_targets": ["Remere's Map Editor", "OpenTibiaBR", "Canary", "TFS", "OTServBR", "OTClient"],
    }
