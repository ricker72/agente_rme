from __future__ import annotations

from typing import Any, Dict, Mapping


def generate_town_metadata(inputs: Mapping[str, Any]) -> Dict[str, Any]:
    blueprint = inputs["CERTIFIED_BLUEPRINT.json"]
    settlements = list(blueprint.get("cities", [])) + list(blueprint.get("villages", []))
    towns = []
    for index, settlement in enumerate(sorted(settlements, key=lambda item: item["id"]), start=1):
        sid = settlement["id"]
        towns.append(
            {
                "town_id": index,
                "settlement_id": sid,
                "name": _title_name(sid),
                "kind": "city" if sid.startswith("city_") else "village",
                "temple_reference": f"temple_anchor_{sid}",
                "protection_zone_anchor": f"pz_anchor_{sid}",
                "logical_only": True,
            }
        )
    return {"artifact": "TOWN_METADATA_MODEL", "logical_only": True, "towns": towns}


def _title_name(value: str) -> str:
    return " ".join(part.capitalize() for part in value.split("_")[1:])
