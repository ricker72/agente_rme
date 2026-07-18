from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, Mapping

from .serializer import xml_to_string


def generate_towns_xml(gameplay: Mapping[str, Any]) -> str:
    root = ET.Element("towns")
    towns = gameplay.get("models", {}).get("towns", {}).get("towns", [])
    for town in sorted(towns, key=lambda item: int(item["town_id"])):
        ET.SubElement(
            root,
            "town",
            {
                "id": str(town["town_id"]),
                "name": str(town["name"]),
                "settlement": str(town["settlement_id"]),
                "temple": str(town.get("temple_reference", "")),
                "protectionZone": str(town.get("protection_zone_anchor", "")),
            },
        )
    return xml_to_string(root)
