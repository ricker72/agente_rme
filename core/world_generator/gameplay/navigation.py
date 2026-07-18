from __future__ import annotations

from typing import Any, Dict, Mapping


def generate_navigation_metadata(waypoints: Mapping[str, Any]) -> Dict[str, Any]:
    nodes = [{"id": node["id"], "accessibility_class": _accessibility(node["kind"])} for node in waypoints["nodes"]]
    edges = []
    for edge in waypoints["edges"]:
        route_type = edge.get("route_type", "road")
        cost = {"main": 1, "road": 2, "secondary": 3, "port": 4}.get(route_type, 2)
        edges.append(
            {
                "id": f"nav_{edge['id']}",
                "from": edge["from"],
                "to": edge["to"],
                "path_weight": cost,
                "travel_cost": cost * 10,
                "accessibility": "public",
            }
        )
    return {"artifact": "NAVIGATION_METADATA_MODEL", "logical_only": True, "nodes": nodes, "edges": edges}


def _accessibility(kind: str) -> str:
    if kind in {"settlement", "port"}:
        return "public_safe"
    if kind == "dungeon_entrance":
        return "adventure"
    return "public"
