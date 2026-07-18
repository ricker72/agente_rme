from __future__ import annotations

from typing import Any, Dict, Mapping


def evaluate_gameplay_constraints(models: Mapping[str, Any]) -> Dict[str, Any]:
    town_ids = {town["settlement_id"] for town in models["towns"]["towns"]}
    waypoint_refs = {node["ref"] for node in models["waypoints"]["nodes"]}
    invalid_town_refs = sorted(town_ids - waypoint_refs)
    duplicate_zones = _duplicates(zone["id"] for zone in models["zones"]["zones"])
    disconnected_navigation = len(models["navigation"]["nodes"]) > 1 and len(models["navigation"]["edges"]) == 0
    return {
        "artifact": "GAMEPLAY_CONSTRAINTS",
        "logical_only": True,
        "overlapping_gameplay_regions": [],
        "conflicting_metadata": duplicate_zones,
        "invalid_town_references": invalid_town_refs,
        "disconnected_navigation": disconnected_navigation,
        "valid": not duplicate_zones and not invalid_town_refs and not disconnected_navigation,
    }


def _duplicates(values) -> list[str]:
    seen = set()
    dupes = set()
    for value in values:
        if value in seen:
            dupes.add(value)
        seen.add(value)
    return sorted(dupes)
