from __future__ import annotations

from typing import Any, Dict, Mapping


def generate_spawn_regions(inputs: Mapping[str, Any], regions: Mapping[str, Any]) -> Dict[str, Any]:
    blueprint = inputs["CERTIFIED_BLUEPRINT.json"]
    spawn_regions = []
    for region in regions["regions"]:
        spawn_regions.append(
            {
                "id": f"spawn_region_{region['region_id']}",
                "region_id": region["region_id"],
                "spawn_policy": "metadata_only",
                "monsters_placed": False,
                "logical_only": True,
            }
        )
    hunts = blueprint.get("gameplay_graph", {}).get("hunts", [])
    for hunt in sorted(hunts, key=_hunt_id):
        hunt_ref = _hunt_id(hunt)
        spawn_regions.append({"id": f"spawn_anchor_{hunt_ref}", "hunt_ref": hunt_ref, "monsters_placed": False, "logical_only": True})
    return {"artifact": "SPAWN_REGION_MODEL", "logical_only": True, "spawn_regions": spawn_regions}


def _hunt_id(hunt) -> str:
    if isinstance(hunt, dict):
        return str(hunt.get("id") or hunt.get("region") or hunt)
    return str(hunt)
