from __future__ import annotations

import struct
from dataclasses import asdict, dataclass
from typing import Tuple

from .attributes import ATTR_DESCRIPTION, write_string
from .chunker import TileArea, chunk_tile_areas
from .header import OtbmHeader, build_header
from .model import OtbmWorldModel

NODE_ROOT = 0x00
NODE_MAP_DATA = 0x02
NODE_TILE_AREA = 0x04
NODE_TOWNS = 0x0C
NODE_TOWN = 0x0D
NODE_WAYPOINTS = 0x0F
NODE_WAYPOINT = 0x10
ATTR_EXT_SPAWN_MONSTER_FILE = 0x0B
ATTR_EXT_HOUSE_FILE = 0x0D
ATTR_EXT_SPAWN_NPC_FILE = 0x17
ATTR_EXT_ZONE_FILE = 0x18


@dataclass(frozen=True)
class OtbmNode:
    node_type: int
    attributes: bytes = b""
    children: Tuple["OtbmNode", ...] = ()

    def to_json_dict(self) -> dict:
        return {
            "node_type": self.node_type,
            "attributes_hex": self.attributes.hex(),
            "children": [child.to_json_dict() for child in self.children],
        }


@dataclass(frozen=True)
class OtbmNodeTree:
    header: OtbmHeader
    root: OtbmNode
    tile_areas: Tuple[TileArea, ...]

    def to_json_dict(self) -> dict:
        return {
            "header": asdict(self.header),
            "root": self.root.to_json_dict(),
            "tile_area_count": len(self.tile_areas),
        }


def build_node_tree(world: OtbmWorldModel) -> OtbmNodeTree:
    from .tile_encoder import tile_to_node

    header = build_header(world.width, world.height)
    areas = chunk_tile_areas(world)
    area_nodes = []
    for area in areas:
        attrs = struct.pack("<HHB", area.base_x, area.base_y, area.z)
        children = tuple(tile_to_node(tile, area.base_x, area.base_y) for tile in area.tiles)
        area_nodes.append(OtbmNode(node_type=NODE_TILE_AREA, attributes=attrs, children=children))

    map_children = tuple(area_nodes) + _towns_node(world) + _waypoints_node(world)
    map_attrs = _map_data_attributes(world)
    map_data = OtbmNode(node_type=NODE_MAP_DATA, attributes=map_attrs, children=map_children)
    root = OtbmNode(node_type=NODE_ROOT, attributes=header.to_bytes(), children=(map_data,))
    return OtbmNodeTree(header=header, root=root, tile_areas=areas)


def _map_data_attributes(world: OtbmWorldModel) -> bytes:
    metadata = world.metadata or {}
    description = str(metadata.get("description") or "WGL-08 deterministic OTBM world")
    spawn_file = str(metadata.get("spawn_monster_file") or "")
    npc_file = str(metadata.get("spawn_npc_file") or "")
    house_file = str(metadata.get("house_file") or "")
    zone_file = str(metadata.get("zone_file") or "")

    out = bytearray()
    attributes = (
        (ATTR_DESCRIPTION, "Saved with RME Agent AI using Canary-compatible OTBM layout"),
        (ATTR_DESCRIPTION, description),
        (ATTR_EXT_SPAWN_MONSTER_FILE, spawn_file),
        (ATTR_EXT_SPAWN_NPC_FILE, npc_file),
        (ATTR_EXT_HOUSE_FILE, house_file),
        (ATTR_EXT_ZONE_FILE, zone_file),
    )
    for attr, value in attributes:
        if attr != ATTR_DESCRIPTION and not value:
            continue
        out.append(attr)
        out.extend(write_string(value))
    return bytes(out)


def _towns_node(world: OtbmWorldModel) -> Tuple[OtbmNode, ...]:
    children = []
    for town in sorted(world.towns, key=lambda item: (int(item.get("id", 0)), str(item.get("name", "")))):
        attrs = struct.pack("<I", int(town["id"])) + write_string(str(town["name"]))
        temple = town.get("temple") or {}
        attrs += struct.pack("<HHB", int(temple["x"]), int(temple["y"]), int(temple["z"]))
        children.append(OtbmNode(node_type=NODE_TOWN, attributes=attrs))
    return (OtbmNode(node_type=NODE_TOWNS, children=tuple(children)),) if children else ()


def _waypoints_node(world: OtbmWorldModel) -> Tuple[OtbmNode, ...]:
    children = []
    for waypoint in sorted(world.waypoints, key=lambda item: str(item.get("name", ""))):
        attrs = write_string(str(waypoint["name"]))
        attrs += struct.pack("<HHB", int(waypoint["x"]), int(waypoint["y"]), int(waypoint["z"]))
        children.append(OtbmNode(node_type=NODE_WAYPOINT, attributes=attrs))
    return (OtbmNode(node_type=NODE_WAYPOINTS, children=tuple(children)),) if children else ()
