from __future__ import annotations

from typing import Any, Dict, Mapping


def generate_gameplay_zones(towns: Mapping[str, Any], regions: Mapping[str, Any]) -> Dict[str, Any]:
    zones = []
    for town in towns["towns"]:
        zones.append(
            {
                "id": f"zone_protection_{town['settlement_id']}",
                "kind": "Protection Zone",
                "reference": town["protection_zone_anchor"],
                "pvp_allowed": False,
                "logical_only": True,
            }
        )
        zones.append(
            {
                "id": f"zone_no_pvp_{town['settlement_id']}",
                "kind": "No-PVP Zone",
                "reference": town["settlement_id"],
                "pvp_allowed": False,
                "logical_only": True,
            }
        )
    for region in regions["regions"]:
        classes = set(region["classes"])
        kind = "Safe Area" if classes & {"cities", "villages"} else "Wilderness Area"
        zones.append(
            {
                "id": f"zone_{region['region_id']}",
                "kind": kind,
                "reference": region["region_id"],
                "pvp_allowed": kind == "Wilderness Area",
                "logical_only": True,
            }
        )
    return {"artifact": "GAMEPLAY_ZONE_MODEL", "logical_only": True, "zones": sorted(zones, key=lambda item: item["id"])}
