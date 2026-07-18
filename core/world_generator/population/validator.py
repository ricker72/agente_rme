from __future__ import annotations

from typing import Any, Dict, Mapping


def validate_population(models: Mapping[str, Any]) -> Dict[str, Any]:
    errors = []
    for key in ("population", "npcs", "ecosystems", "spawns", "services", "factions", "economy", "constraints"):
        if not models.get(key):
            errors.append(f"missing {key}")
    if not models["npcs"]["npcs"]:
        errors.append("no NPC metadata")
    if not models["ecosystems"]["ecosystems"]:
        errors.append("no ecosystem metadata")
    if not models["spawns"]["distributions"]:
        errors.append("no spawn distribution metadata")
    if not models["factions"]["factions"]:
        errors.append("no faction metadata")
    if not models["economy"]["trade_routes"]:
        errors.append("no economy routes")
    if not models["constraints"]["valid"]:
        errors.append("population constraints failed")
    metrics = _metrics(models, not errors)
    return {"artifact": "POPULATION_VALIDATION", "logical_only": True, "valid": not errors, "errors": errors, "metrics": metrics}


def _metrics(models: Mapping[str, Any], valid: bool) -> Dict[str, float]:
    ecosystem = 1.0 if models["ecosystems"]["ecosystems"] else 0.0
    npc = 1.0 if models["npcs"]["npcs"] else 0.0
    spawn = 1.0 if models["spawns"]["distributions"] and all(not item["monsters_placed"] for item in models["spawns"]["distributions"]) else 0.0
    faction = 1.0 if models["factions"]["factions"] and models["constraints"]["valid"] else 0.0
    service = 1.0 if models["services"]["services"] else 0.0
    pqi = (float(valid) + ecosystem + npc + spawn + faction + service) / 6
    return {
        "PQI": round(pqi, 6),
        "ECI2": ecosystem,
        "NCI2": npc,
        "SDI": spawn,
        "FSI": faction,
        "SEI": service,
    }
