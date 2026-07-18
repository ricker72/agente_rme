from __future__ import annotations

from typing import Any, Dict, Mapping


def generate_house_metadata(inputs: Mapping[str, Any]) -> Dict[str, Any]:
    structure = inputs["CERTIFIED_STRUCTURE_LAYOUT.json"]
    parcels = structure.get("parcel_model", {}).get("parcels", [])
    houses = []
    for index, parcel in enumerate(sorted(parcels, key=lambda item: item["id"]), start=1):
        settlement = parcel.get("settlement") or _settlement_from_id(parcel["id"])
        houses.append(
            {
                "house_id": index,
                "parcel_id": parcel["id"],
                "ownership_region": settlement,
                "building_classification": _classify(parcel),
                "residential_group": f"residential_group_{settlement}",
                "ownership_file_generated": False,
                "logical_only": True,
            }
        )
    return {"artifact": "HOUSE_METADATA_MODEL", "logical_only": True, "houses": houses}


def _settlement_from_id(value: str) -> str:
    parts = value.split("_")
    return "_".join(parts[1:-1]) if len(parts) > 2 else value


def _classify(parcel: Mapping[str, Any]) -> str:
    role = str(parcel.get("classification") or parcel.get("role") or parcel.get("intended_use") or "residential")
    if "market" in role or "commerce" in role:
        return "commercial"
    if "temple" in role or "civic" in role:
        return "civic"
    return "residential"
