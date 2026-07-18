from __future__ import annotations

from typing import Any, Dict, Mapping


def optimize_population(models: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "artifact": "POPULATION_OPTIMIZATION",
        "logical_only": True,
        "ecosystem_balance": "balanced" if models["ecosystems"]["ecosystems"] else "empty",
        "npc_coverage": "complete" if models["npcs"]["npcs"] else "empty",
        "service_accessibility": "complete" if models["services"]["services"] else "empty",
        "regional_diversity": "diverse" if len(models["ecosystems"]["ecosystems"]) >= 2 else "limited",
        "travel_efficiency": "aligned_with_infrastructure",
        "valid": models["constraints"]["valid"],
    }
