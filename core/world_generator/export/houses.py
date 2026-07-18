from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, Mapping

from .serializer import xml_to_string


def generate_houses_xml(gameplay: Mapping[str, Any]) -> str:
    root = ET.Element("houses")
    houses = gameplay.get("models", {}).get("houses", {}).get("houses", [])
    for house in sorted(houses, key=lambda item: int(item["house_id"])):
        exit_position = house.get("exit_position") or house.get("exit") or {}
        if isinstance(exit_position, (list, tuple)):
            exit_position = dict(zip(("x", "y", "z"), exit_position))
        house_id = str(house["house_id"])
        ET.SubElement(
            root,
            "house",
            {
                "id": house_id,
                "houseid": house_id,
                "name": str(house["parcel_id"]),
                "region": str(house["ownership_region"]),
                "classification": str(house["building_classification"]),
                "owner": "0",
                "entryx": str(exit_position.get("x", 0)),
                "entryy": str(exit_position.get("y", 0)),
                "entryz": str(exit_position.get("z", 0)),
                "rent": str(house.get("rent", 0)),
                "townid": str(house.get("town_id", 1)),
                "size": str(house.get("tile_count", house.get("size", 0))),
                "clientid": str(house.get("client_id", 0)),
                "beds": str(house.get("beds", 0)),
            },
        )
    return xml_to_string(root)
