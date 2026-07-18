from __future__ import annotations

from typing import Any, Dict, Mapping

SERVICE_ROLES = ("banker", "blacksmith", "guard", "merchant", "priest", "trainer")
PORT_ROLES = ("ferryman",)
CITY_EXTRA_ROLES = ("guild_master", "service_npc")


def plan_npc_population(inputs: Mapping[str, Any]) -> Dict[str, Any]:
    gameplay = inputs["CERTIFIED_GAMEPLAY_METADATA.json"]
    towns = gameplay.get("models", {}).get("towns", {}).get("towns", [])
    npc_population = []
    for town in sorted(towns, key=lambda item: item["settlement_id"]):
        roles = list(SERVICE_ROLES)
        if town.get("kind") == "city":
            roles.extend(CITY_EXTRA_ROLES)
        if "sunport" in town["settlement_id"] or "oasis" in town["settlement_id"]:
            roles.extend(PORT_ROLES)
        for index, role in enumerate(sorted(set(roles)), start=1):
            npc_population.append(
                {
                    "id": f"npc_meta_{town['settlement_id']}_{role}",
                    "role": role,
                    "settlement_id": town["settlement_id"],
                    "town_id": town["town_id"],
                    "placement_policy": "logical_metadata_only",
                    "written_to_otbm": False,
                    "lua_generated": False,
                    "priority": index,
                }
            )
    return {"artifact": "NPC_POPULATION_MODEL", "logical_only": True, "npcs": npc_population}
