from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, Mapping

from .serializer import xml_to_string


def generate_waypoints_xml(gameplay: Mapping[str, Any]) -> str:
    root = ET.Element("waypoints")
    graph = gameplay.get("models", {}).get("waypoints", {})
    for node in sorted(graph.get("nodes", []), key=lambda item: item["id"]):
        ET.SubElement(root, "waypoint", {"id": str(node["id"]), "kind": str(node["kind"]), "ref": str(node["ref"])})
    for edge in sorted(graph.get("edges", []), key=lambda item: item["id"]):
        ET.SubElement(
            root,
            "edge",
            {"id": str(edge["id"]), "from": str(edge["from"]), "to": str(edge["to"]), "type": str(edge.get("route_type", "road"))},
        )
    return xml_to_string(root)
