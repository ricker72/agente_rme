from __future__ import annotations

from typing import Any, Dict, Mapping


def classify_regions(inputs: Mapping[str, Any]) -> Dict[str, Any]:
    blueprint = inputs["CERTIFIED_BLUEPRINT.json"]
    civilization = inputs["CERTIFIED_CIVILIZATION_MODEL.json"]
    infrastructure = inputs["CERTIFIED_INFRASTRUCTURE_GRAPH.json"]
    districts = civilization.get("district_model", {}).get("districts", [])
    ports = infrastructure.get("port_transport_model", {}).get("ports", [])
    classifications = []
    for region in sorted(blueprint.get("regions", []), key=lambda item: item["id"]):
        rid = region["id"]
        classifications.append(
            {
                "region_id": rid,
                "classes": sorted(set(_classes_for_region(rid, blueprint, districts, ports))),
                "logical_only": True,
            }
        )
    return {"artifact": "REGION_CLASSIFICATION_MODEL", "logical_only": True, "regions": classifications}


def _classes_for_region(region_id: str, blueprint: Mapping[str, Any], districts: list, ports: list) -> list[str]:
    classes = ["wilderness"]
    if any(item.get("region") == region_id for item in blueprint.get("cities", [])):
        classes.append("cities")
    if any(item.get("region") == region_id for item in blueprint.get("villages", [])):
        classes.append("villages")
    if any(item.get("region") == region_id for item in blueprint.get("dungeons", [])):
        classes.append("dungeon_regions")
    if any(item.get("region") == region_id for item in ports):
        classes.extend(["ports", "coastline"])
    if "snow" in region_id:
        classes.append("mountains")
    if "desert" in region_id:
        classes.append("industrial_districts")
    if any(d.get("role") in {"temple", "religious"} for d in districts):
        classes.append("religious_districts")
    return classes
