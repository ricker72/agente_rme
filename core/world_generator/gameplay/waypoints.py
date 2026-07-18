from __future__ import annotations

from typing import Any, Dict, Mapping


def generate_waypoint_graph(inputs: Mapping[str, Any], towns: Mapping[str, Any], regions: Mapping[str, Any]) -> Dict[str, Any]:
    infrastructure = inputs["CERTIFIED_INFRASTRUCTURE_GRAPH.json"]
    blueprint = inputs["CERTIFIED_BLUEPRINT.json"]
    nodes = []
    for town in towns["towns"]:
        nodes.append({"id": f"wp_{town['settlement_id']}", "kind": "settlement", "ref": town["settlement_id"]})
    for dungeon in sorted(blueprint.get("dungeons", []), key=lambda item: item["id"]):
        nodes.append({"id": f"wp_{dungeon['id']}", "kind": "dungeon_entrance", "ref": dungeon["id"]})
    for port in sorted(infrastructure.get("port_transport_model", {}).get("ports", []), key=lambda item: item["id"]):
        nodes.append({"id": f"wp_{port['id']}", "kind": "port", "ref": port["id"]})
    for region in regions["regions"]:
        nodes.append({"id": f"wp_{region['region_id']}", "kind": "landmark", "ref": region["region_id"]})

    edges = []
    for edge in sorted(infrastructure.get("route_graph_model", {}).get("edges", []), key=lambda item: item["id"]):
        edges.append(
            {
                "id": f"waypoint_edge_{edge['id']}",
                "from": f"wp_{edge.get('from')}",
                "to": f"wp_{edge.get('to')}",
                "route_type": edge.get("route_type") or edge.get("type", "road"),
                "logical_only": True,
            }
        )
    return {"artifact": "WAYPOINT_GRAPH_MODEL", "logical_only": True, "nodes": nodes, "edges": edges}
