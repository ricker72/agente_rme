from __future__ import annotations

from typing import Any, Dict, Mapping


def plan_factions(inputs: Mapping[str, Any]) -> Dict[str, Any]:
    blueprint = inputs["CERTIFIED_BLUEPRINT.json"]
    factions = []
    for city in sorted(blueprint.get("cities", []), key=lambda item: item["id"]):
        factions.append({"id": f"faction_{city['id']}", "owner_ref": city["id"], "territory_type": "city", "stability": "stable"})
    for village in sorted(blueprint.get("villages", []), key=lambda item: item["id"]):
        factions.append({"id": f"faction_{village['id']}", "owner_ref": village["id"], "territory_type": "village", "stability": "stable"})
    for region in sorted(blueprint.get("regions", []), key=lambda item: item["id"]):
        factions.append({"id": f"faction_neutral_{region['id']}", "owner_ref": region["id"], "territory_type": "neutral_region", "stability": "neutral"})
    return {"artifact": "FACTION_MODEL", "logical_only": True, "factions": factions}
