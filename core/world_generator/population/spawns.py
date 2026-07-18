from __future__ import annotations

from typing import Any, Dict, Mapping


def plan_spawn_distribution(inputs: Mapping[str, Any], ecosystems: Mapping[str, Any]) -> Dict[str, Any]:
    blueprint = inputs["CERTIFIED_BLUEPRINT.json"]
    distributions = []
    for ecosystem in ecosystems["ecosystems"]:
        distributions.append(
            {
                "id": f"spawn_distribution_{ecosystem['region_id']}",
                "region_id": ecosystem["region_id"],
                "common_creatures": ecosystem["official_reference_names"][:2],
                "elite_creatures": ecosystem["official_reference_names"][2:],
                "boss_region": False,
                "event_region": False,
                "spawn_file_generated": False,
                "monsters_placed": False,
            }
        )
    for boss in sorted(blueprint.get("bosses", []), key=lambda item: item["id"]):
        distributions.append(
            {
                "id": f"boss_distribution_{boss['id']}",
                "boss_ref": boss["id"],
                "dungeon_ref": boss.get("dungeon"),
                "common_creatures": [],
                "elite_creatures": [],
                "boss_region": True,
                "event_region": False,
                "spawn_file_generated": False,
                "monsters_placed": False,
            }
        )
    return {"artifact": "SPAWN_DISTRIBUTION_MODEL", "logical_only": True, "distributions": distributions}
