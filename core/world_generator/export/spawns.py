from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, Mapping

from .serializer import xml_to_string


def generate_spawns_xml(population: Mapping[str, Any]) -> str:
    root = ET.Element("spawns", {"metadataOnly": "true"})
    distributions = population.get("models", {}).get("spawns", {}).get("distributions", [])
    for dist in sorted(distributions, key=lambda item: item["id"]):
        attrs = {
            "id": str(dist["id"]),
            "region": str(dist.get("region_id") or dist.get("dungeon_ref") or ""),
            "bossRegion": str(bool(dist.get("boss_region"))).lower(),
            "monstersPlaced": "false",
        }
        spawn = ET.SubElement(root, "spawnRegion", attrs)
        for name in sorted(dist.get("common_creatures", []) + dist.get("elite_creatures", [])):
            ET.SubElement(spawn, "creatureRef", {"name": str(name)})
    return xml_to_string(root)
