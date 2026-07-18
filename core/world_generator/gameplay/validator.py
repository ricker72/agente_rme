from __future__ import annotations

from typing import Any, Dict, Mapping


def validate_gameplay_metadata(models: Mapping[str, Any]) -> Dict[str, Any]:
    errors = []
    for key in ("semantics", "towns", "houses", "waypoints", "regions", "zones", "spawns", "quests", "navigation"):
        if not models.get(key):
            errors.append(f"missing {key}")
    if not models["towns"]["towns"]:
        errors.append("no town metadata")
    if not models["waypoints"]["nodes"]:
        errors.append("no waypoint nodes")
    if not models["zones"]["zones"]:
        errors.append("no gameplay zones")
    if not models["quests"]["anchors"]:
        errors.append("no quest anchors")
    if not models["navigation"]["nodes"]:
        errors.append("no navigation nodes")
    if not models["constraints"]["valid"]:
        errors.append("gameplay constraints failed")
    metrics = _metrics(models, not errors)
    return {"artifact": "GAMEPLAY_VALIDATION", "logical_only": True, "valid": not errors, "errors": errors, "metrics": metrics}


def _metrics(models: Mapping[str, Any], valid: bool) -> Dict[str, float]:
    has_edges = 1.0 if models["navigation"]["edges"] or len(models["navigation"]["nodes"]) <= 1 else 0.0
    region_integrity = 1.0 if models["regions"]["regions"] else 0.0
    zone_coverage = min(1.0, len(models["zones"]["zones"]) / max(1, len(models["regions"]["regions"])))
    navigation = 1.0 if models["navigation"]["nodes"] else 0.0
    semantic = 1.0 if models["semantics"]["geometry_frozen"] else 0.0
    gqi = (float(valid) + has_edges + region_integrity + zone_coverage + navigation + semantic) / 6
    return {
        "GQI": round(gqi, 6),
        "WCI2": has_edges,
        "RGI": region_integrity,
        "ZCI": round(zone_coverage, 6),
        "NMI": navigation,
        "SQI": semantic,
    }
