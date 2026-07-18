from __future__ import annotations

from typing import Any, Dict, Mapping


def build_population_model(models: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "artifact": "POPULATION_MODEL",
        "logical_only": True,
        "living_world_model": True,
        "counts": {
            "npc_metadata": len(models["npcs"]["npcs"]),
            "ecosystems": len(models["ecosystems"]["ecosystems"]),
            "spawn_distributions": len(models["spawns"]["distributions"]),
            "services": len(models["services"]["services"]),
            "factions": len(models["factions"]["factions"]),
            "trade_routes": len(models["economy"]["trade_routes"]),
        },
        "rules": {
            "otbm_geometry_preserved": True,
            "metadata_only": True,
            "no_lua": True,
            "no_spawn_files": True,
        },
    }
