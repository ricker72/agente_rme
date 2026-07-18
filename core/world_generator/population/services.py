from __future__ import annotations

from typing import Any, Dict, Mapping

SERVICE_TYPES = ("banking", "crafting", "depot", "healing", "temple", "trade", "transport")


def plan_services(inputs: Mapping[str, Any], npcs: Mapping[str, Any]) -> Dict[str, Any]:
    gameplay = inputs["CERTIFIED_GAMEPLAY_METADATA.json"]
    towns = gameplay.get("models", {}).get("towns", {}).get("towns", [])
    npc_roles_by_settlement = {}
    for npc in npcs["npcs"]:
        npc_roles_by_settlement.setdefault(npc["settlement_id"], set()).add(npc["role"])
    services = []
    for town in sorted(towns, key=lambda item: item["settlement_id"]):
        roles = npc_roles_by_settlement.get(town["settlement_id"], set())
        for service in SERVICE_TYPES:
            services.append(
                {
                    "id": f"service_{town['settlement_id']}_{service}",
                    "settlement_id": town["settlement_id"],
                    "service_type": service,
                    "provider_role": _provider(service),
                    "coverage": "available" if _provider(service) in roles or service in {"depot", "temple", "trade"} else "planned",
                    "logical_only": True,
                }
            )
    return {"artifact": "SERVICE_POPULATION_MODEL", "logical_only": True, "services": services}


def _provider(service: str) -> str:
    return {
        "banking": "banker",
        "crafting": "blacksmith",
        "depot": "service_npc",
        "healing": "priest",
        "temple": "priest",
        "trade": "merchant",
        "transport": "ferryman",
    }[service]
