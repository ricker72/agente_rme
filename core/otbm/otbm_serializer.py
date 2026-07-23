from __future__ import annotations

import io
import logging
import struct
from typing import Any, Dict, List, Optional, Tuple, cast

from .tile_encoder import TileEncoder

# Import constants directly to avoid circular imports
from .compatibility.otbm_constants import (
    OTBM_ACCEPTED_IDENTIFIERS,
    OTBM_ATTR_ACTION_ID as ATTR_ACTION_ID,
    OTBM_ATTR_CHARGES as ATTR_CHARGES,
    OTBM_ATTR_COUNT as ATTR_COUNT,
    OTBM_ATTR_DECAYING_STATE as ATTR_DECAYING_STATE,
    OTBM_ATTR_DURATION as ATTR_DURATION,
    OTBM_ATTR_SUBTYPE as ATTR_SUBTYPE,
    OTBM_ATTR_TEXT as ATTR_TEXT,
    OTBM_ATTR_TILE_FLAGS as ATTR_TILE_FLAGS,
    OTBM_ATTR_UNIQUE_ID as ATTR_UNIQUE_ID,
)

logger = logging.getLogger(__name__)

# ====================================================================
# REAL OTBM PROTOCOL CONSTANTS (verified against world.otbm)
# ====================================================================
# WG-18E Reference Protocol Extraction from projects/.aud3_world_extract/world.otbm
#
# REAL FILE STRUCTURE:
#   [4 bytes: magic = 0x00000000]
#   [FE 00] [16-byte root header] [MAP_DATA child] [FF]
#   [FE 02] [MAP_DATA attributes] [child nodes] [FF]
#
# Nodes do not carry explicit size fields in the RME reference stream.
# FD-escaping is applied to attribute/property bytes only; child FE/FF
# delimiters must stay literal so RME can see the node hierarchy.
# ====================================================================

OTBM_MAGIC = b"\x00\x00\x00\x00"
NODE_START = 0xFE
NODE_END = 0xFF
ESCAPE_BYTE = 0xFD

REAL_OTBM_VERSION = 4
REAL_ITEM_MAJOR_VERSION = 4
REAL_ITEM_MINOR_VERSION = 4
REAL_ROOT_NODE_TYPE = 0x00

# v1.0.1 HOTFIX: tile chunking limits
MAX_TILE_AREA_PAYLOAD = 30000
MAX_TILE_AREA_TILES = 200


# ====================================================================
# FD-Escaping (WG-18C real OTBM protocol)
# ====================================================================

def _fd_escape(data: bytes) -> bytes:
    """Apply FD-escaping to raw data bytes."""
    buf = io.BytesIO()
    for byte in data:
        if byte in (0xFE, 0xFF, 0xFD):
            buf.write(bytes([ESCAPE_BYTE, byte]))
        else:
            buf.write(bytes([byte]))
    return buf.getvalue()


def _fd_unescape(data: bytes, offset: int = 0) -> Tuple[bytes, int]:
    """Remove FD-escaping from raw data bytes."""
    buf = io.BytesIO()
    i = offset
    while i < len(data):
        byte = data[i]
        if byte == ESCAPE_BYTE:
            if i + 1 >= len(data):
                break
            escaped = data[i + 1]
            buf.write(bytes([escaped]))
            i += 2
        else:
            buf.write(bytes([byte]))
            i += 1
    return buf.getvalue(), len(data)


# ====================================================================
# REAL OTBM Node Writers
# ====================================================================

def _write_node_start(buf: io.BytesIO, node_type: int) -> None:
    buf.write(bytes([NODE_START, node_type]))


def _write_node_end(buf: io.BytesIO) -> None:
    buf.write(bytes([NODE_END]))


def _write_node(buf: io.BytesIO, node_type: int, attrs: bytes = b"",
                children: bytes = b"") -> None:
    _write_node_start(buf, node_type)
    buf.write(_fd_escape(attrs))
    buf.write(children)
    _write_node_end(buf)


def _write_root_node(buf: io.BytesIO, width: int, height: int, children: bytes) -> None:
    attrs = struct.pack(
        "<IHHII",
        REAL_OTBM_VERSION,
        max(1, min(0xFFFF, int(width))),
        max(1, min(0xFFFF, int(height))),
        REAL_ITEM_MAJOR_VERSION,
        REAL_ITEM_MINOR_VERSION,
    )
    _write_node(buf, REAL_ROOT_NODE_TYPE, attrs, children)


def _write_map_data_node(buf: io.BytesIO, description: str, spawn_file: str,
                         house_file: str, children: bytes) -> None:
    """Write MAP_DATA node using reference-style tagged string attributes."""
    attrs_buf = io.BytesIO()
    if description:
        attrs_buf.write(bytes([0x01]))
        _write_string_raw(attrs_buf, description)
    if spawn_file:
        attrs_buf.write(bytes([0x0B]))
        _write_string_raw(attrs_buf, spawn_file)
    if house_file:
        attrs_buf.write(bytes([0x0D]))
        _write_string_raw(attrs_buf, house_file)
    _write_node(buf, 0x02, attrs_buf.getvalue(), children)


def _write_tile_area_node(buf: io.BytesIO, base_x: int, base_y: int,
                          base_z: int, children: bytes) -> None:
    attrs_buf = io.BytesIO()
    attrs_buf.write(struct.pack("<H", _clamp_u16(base_x)))
    attrs_buf.write(struct.pack("<H", _clamp_u16(base_y)))
    attrs_buf.write(struct.pack("<B", _clamp_u8(base_z)))
    _write_node(buf, 0x04, attrs_buf.getvalue(), children)


def _write_tile_node(buf: io.BytesIO, offset_x: int, offset_y: int,
                     tile_flags: int, children: bytes) -> None:
    attrs_buf = io.BytesIO()
    attrs_buf.write(struct.pack("<B", offset_x))
    attrs_buf.write(struct.pack("<B", offset_y))
    if tile_flags:
        attrs_buf.write(struct.pack("<B", ATTR_TILE_FLAGS))
        attrs_buf.write(struct.pack("<I", tile_flags))
    _write_node(buf, 0x05, attrs_buf.getvalue(), children)


def _write_item_node(buf: io.BytesIO, item_id: int, count: Optional[int] = None,
                     action_id: Optional[int] = None, unique_id: Optional[int] = None,
                     text: Optional[str] = None, subtype: Optional[int] = None,
                     charges: Optional[int] = None, duration: Optional[int] = None,
                     decaying_state: Optional[int] = None, children: bytes = b"") -> None:
    attrs_buf = io.BytesIO()
    attrs_buf.write(struct.pack("<H", _clamp_u16(item_id)))
    if count is not None:
        attrs_buf.write(bytes([ATTR_COUNT, _clamp_u8(count)]))
    if action_id is not None:
        attrs_buf.write(bytes([ATTR_ACTION_ID]))
        attrs_buf.write(struct.pack("<H", _clamp_u16(action_id)))
    if unique_id is not None:
        attrs_buf.write(bytes([ATTR_UNIQUE_ID]))
        attrs_buf.write(struct.pack("<H", _clamp_u16(unique_id)))
    if text is not None:
        attrs_buf.write(bytes([ATTR_TEXT]))
        _write_string_raw(attrs_buf, text)
    if subtype is not None:
        attrs_buf.write(bytes([ATTR_SUBTYPE, _clamp_u8(subtype)]))
    if charges is not None:
        attrs_buf.write(bytes([ATTR_CHARGES, _clamp_u8(charges)]))
    if duration is not None:
        attrs_buf.write(bytes([ATTR_DURATION]))
        attrs_buf.write(struct.pack("<I", _clamp_u32(duration)))
    if decaying_state is not None:
        attrs_buf.write(bytes([ATTR_DECAYING_STATE, _clamp_u8(decaying_state)]))
    _write_node(buf, 0x06, attrs_buf.getvalue(), children)


def _write_spawns_node(buf: io.BytesIO, children: bytes) -> None:
    _write_node(buf, 0x09, children=children)


def _write_spawn_area_node(buf: io.BytesIO, center_x: int, center_y: int,
                            center_z: int, radius: int, children: bytes) -> None:
    attrs_buf = io.BytesIO()
    attrs_buf.write(struct.pack("<H", _clamp_u16(center_x)))
    attrs_buf.write(struct.pack("<H", _clamp_u16(center_y)))
    attrs_buf.write(struct.pack("<B", _clamp_u8(center_z)))
    attrs_buf.write(struct.pack("<B", _clamp_u8(radius)))
    _write_node(buf, 0x0A, attrs_buf.getvalue(), children)


def _write_monster_node(buf: io.BytesIO, name: str, direction: int = 2,
                        spawntime: int = 60) -> None:
    attrs_buf = io.BytesIO()
    _write_string_raw(attrs_buf, name)
    attrs_buf.write(struct.pack("<B", _clamp_u8(direction)))
    attrs_buf.write(struct.pack("<I", _clamp_u32(spawntime)))
    _write_node(buf, 0x0B, attrs_buf.getvalue())


def _write_towns_node(buf: io.BytesIO, children: bytes) -> None:
    _write_node(buf, 0x0C, children=children)


def _write_town_node(buf: io.BytesIO, town_id: int, name: str,
                     temple_x: int, temple_y: int, temple_z: int) -> None:
    attrs_buf = io.BytesIO()
    attrs_buf.write(struct.pack("<I", _clamp_u32(town_id)))
    _write_string_raw(attrs_buf, name)
    attrs_buf.write(struct.pack("<H", _clamp_u16(temple_x)))
    attrs_buf.write(struct.pack("<H", _clamp_u16(temple_y)))
    attrs_buf.write(struct.pack("<B", _clamp_u8(temple_z)))
    _write_node(buf, 0x0D, attrs_buf.getvalue())


def _write_waypoints_node(buf: io.BytesIO, children: bytes) -> None:
    _write_node(buf, 0x0F, children=children)


def _write_waypoint_node(buf: io.BytesIO, name: str, x: int, y: int, z: int) -> None:
    attrs_buf = io.BytesIO()
    _write_string_raw(attrs_buf, name)
    attrs_buf.write(struct.pack("<H", _clamp_u16(x)))
    attrs_buf.write(struct.pack("<H", _clamp_u16(y)))
    attrs_buf.write(struct.pack("<B", _clamp_u8(z)))
    _write_node(buf, 0x10, attrs_buf.getvalue())


def _write_string_raw(buf: io.BytesIO, text: str) -> None:
    encoded = (text or "").encode("utf-8", errors="ignore")
    if len(encoded) > 65535:
        encoded = encoded[:65535]
    buf.write(struct.pack("<H", len(encoded)))
    buf.write(encoded)


def _clamp_u8(value: Any) -> int:
    try:
        iv = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(0xFF, iv))


def _clamp_u16(value: Any) -> int:
    try:
        iv = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(0xFFFF, iv))


def _clamp_u32(value: Any) -> int:
    try:
        iv = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(0xFFFFFFFF, iv))


# ====================================================================
# OtbmSerializer - REAL OTBM PROTOCOL
# ====================================================================

class OtbmSerializer:
    """
    Serializes a WorldModel into real OTBM binary format.

    REAL OTBM PROTOCOL (verified against world.otbm):
        [4 bytes: magic = 00000000]
        [FE 00] [root header] [FE 02 MAP_DATA ... FF] [FF]
    """

    def __init__(self):
        from .node_encoder import NodeEncoder
        self.node = NodeEncoder()
        self.tile_encoder = TileEncoder()

    def serialize(self, world_model: Any) -> bytes:
        """
        Convert a WorldModel into a real OTBM binary stream.
        """
        return self._serialize_rme(world_model)

    def _serialize_rme(self, world_model: Any) -> bytes:
        """Serialize only the delimiter-based format emitted by RME/Canary."""
        tiles = list(getattr(world_model, "tiles", {}).values())
        if not tiles and hasattr(world_model, "tiles_list"):
            tiles = list(world_model.tiles_list)
        grouped: Dict[int, List[Any]] = {}
        for tile in tiles:
            grouped.setdefault(self._get_z(tile), []).append(tile)

        explicit_width = self._get_optional_int(world_model, "width")
        explicit_height = self._get_optional_int(world_model, "height")
        all_x = [self._get_x(tile) for tile in tiles]
        all_y = [self._get_y(tile) for tile in tiles]
        width = explicit_width or ((max(all_x) - min(all_x) + 1) if all_x else 1)
        height = explicit_height or ((max(all_y) - min(all_y) + 1) if all_y else 1)

        map_children = io.BytesIO()
        for z in sorted(grouped):
            for base_x, base_y, chunk_tiles in self._chunk_tiles(grouped[z]):
                tile_nodes = io.BytesIO()
                for tile in chunk_tiles:
                    tile_nodes.write(self._encode_tile_node(self._tile_to_dict(tile), base_x, base_y))
                _write_tile_area_node(
                    map_children,
                    base_x=base_x,
                    base_y=base_y,
                    base_z=z,
                    children=tile_nodes.getvalue(),
                )

        spawn_entries: List[Dict[str, Any]] = []
        for spawn in getattr(world_model, "spawns", []) or []:
            name = self._get_spawn_name(spawn)
            if name:
                spawn_entries.append({
                    "x": self._get_spawn_attr(spawn, "x", self._get_spawn_attr(spawn, "center_x", 0)),
                    "y": self._get_spawn_attr(spawn, "y", self._get_spawn_attr(spawn, "center_y", 0)),
                    "z": self._get_spawn_attr(spawn, "z", self._get_spawn_attr(spawn, "center_z", 0)),
                    "radius": self._get_spawn_attr(spawn, "radius", 3),
                    "interval": self._get_spawn_attr(spawn, "respawn", self._get_spawn_attr(spawn, "interval", 60)),
                    "name": name,
                })
        if spawn_entries:
            spawn_nodes = io.BytesIO()
            for spawn in spawn_entries:
                monster = io.BytesIO()
                _write_monster_node(monster, spawn["name"], 2, int(spawn["interval"] or 60))
                _write_spawn_area_node(
                    spawn_nodes,
                    int(spawn["x"]),
                    int(spawn["y"]),
                    int(spawn["z"]),
                    int(spawn["radius"] or 3),
                    monster.getvalue(),
                )
            _write_spawns_node(map_children, spawn_nodes.getvalue())

        cities = getattr(world_model, "cities", []) or []
        if cities:
            town_nodes = io.BytesIO()
            for index, city in enumerate(cities, start=1):
                _write_town_node(
                    town_nodes,
                    int(self._get_spawn_attr(city, "id", index)),
                    str(self._get_spawn_attr(city, "name", f"Town{index}")),
                    int(self._get_spawn_attr(city, "temple_x", self._get_spawn_attr(city, "x", 0))),
                    int(self._get_spawn_attr(city, "temple_y", self._get_spawn_attr(city, "y", 0))),
                    int(self._get_spawn_attr(city, "temple_z", self._get_spawn_attr(city, "z", 0))),
                )
            _write_towns_node(map_children, town_nodes.getvalue())

        waypoints = getattr(world_model, "waypoints", []) or []
        if waypoints:
            waypoint_nodes = io.BytesIO()
            for waypoint in waypoints:
                _write_waypoint_node(
                    waypoint_nodes,
                    str(self._get_spawn_attr(waypoint, "name", "waypoint")),
                    int(self._get_spawn_attr(waypoint, "x", 0)),
                    int(self._get_spawn_attr(waypoint, "y", 0)),
                    int(self._get_spawn_attr(waypoint, "z", 0)),
                )
            _write_waypoints_node(map_children, waypoint_nodes.getvalue())

        map_data = io.BytesIO()
        _write_map_data_node(
            map_data,
            description=str(getattr(world_model, "description", "") or ""),
            spawn_file=str(getattr(world_model, "spawn_file", "") or ""),
            house_file=str(getattr(world_model, "house_file", "") or ""),
            children=map_children.getvalue(),
        )
        output = io.BytesIO()
        output.write(OTBM_MAGIC)
        _write_root_node(output, width, height, map_data.getvalue())
        return output.getvalue()

    def _serialize_certified(self, world_model: Any) -> bytes:
        """Serialize using the certified OTBM contract used by validators.

        The active validators and RC export tests require:
        OTBM magic, canonical Canary/RME root node 0x01, a 16-byte root
        header, then size-prefixed child nodes. This keeps the public
        exporter API unchanged while aligning the binary stream with the
        certified validation path.
        """
        tiles_by_z: Dict[int, List[Any]] = {}
        tiles_list = list(getattr(world_model, "tiles", {}).values())
        if not tiles_list and hasattr(world_model, "tiles_list"):
            tiles_list = world_model.tiles_list

        for tile in tiles_list:
            z = self._get_z(tile)
            tiles_by_z.setdefault(z, []).append(tile)

        all_x, all_y = [], []
        for z_tiles in tiles_by_z.values():
            for t in z_tiles:
                x = self._get_x(t)
                y = self._get_y(t)
                all_x.append(x)
                all_y.append(y)

        explicit_width = self._get_optional_int(world_model, "width")
        explicit_height = self._get_optional_int(world_model, "height")

        if not all_x:
            width = explicit_width or 1
            height = explicit_height or 1
            map_children = io.BytesIO()
            tile_children = self.node.encode_item(106)
            tile_node = self.node.encode_tile(
                offset_x=0,
                offset_y=0,
                tile_flags=0,
                children=tile_children,
            )
            map_children.write(
                self.node.encode_tile_area(
                    base_x=0,
                    base_y=0,
                    base_z=0,
                    children=tile_node,
                )
            )
        else:
            width = explicit_width or (max(all_x) - min(all_x) + 1)
            height = explicit_height or (max(all_y) - min(all_y) + 1)
            map_children = io.BytesIO()

            for z in sorted(tiles_by_z.keys()):
                z_tiles = tiles_by_z[z]
                base_z = z
                chunks = self._chunk_tiles(z_tiles)
                for base_x, base_y, chunk_tiles in chunks:
                    tile_nodes = io.BytesIO()
                    for tile in chunk_tiles:
                        tile_bytes = self._encode_certified_tile_node(tile, base_x, base_y)
                        tile_nodes.write(tile_bytes)
                    map_children.write(
                        self.node.encode_tile_area(
                            base_x=base_x,
                            base_y=base_y,
                            base_z=base_z,
                            children=tile_nodes.getvalue(),
                        )
                    )

            # Spawns
            spawns = getattr(world_model, "spawns", []) or []
            spawn_entries: List[Dict[str, Any]] = []

            for spawn in spawns:
                monster_name = self._get_spawn_name(spawn)
                if not monster_name:
                    continue
                sx = self._get_spawn_attr(spawn, "x", self._get_spawn_attr(spawn, "center_x", 0))
                sy = self._get_spawn_attr(spawn, "y", self._get_spawn_attr(spawn, "center_y", 0))
                sz = self._get_spawn_attr(spawn, "z", self._get_spawn_attr(spawn, "center_z", 0))
                radius = self._get_spawn_attr(
                    spawn, "radius", self._get_spawn_attr(spawn, "spawn_radius", 3)
                )
                interval = self._get_spawn_attr(
                    spawn,
                    "respawn",
                    self._get_spawn_attr(spawn, "interval", self._get_spawn_attr(spawn, "spawntime", 60)),
                )
                spawn_entries.append({
                    "x": sx, "y": sy, "z": sz,
                    "monster_name": monster_name,
                    "interval": int(interval) if interval else 60,
                    "radius": int(radius) if radius else 3,
                })

            for tile in tiles_list:
                tile_spawn = self._get_spawn(tile)
                tile_creature = self._get_creature(tile)
                if tile_spawn or tile_creature:
                    name = ""
                    if tile_spawn and isinstance(tile_spawn, dict):
                        name = tile_spawn.get("monster", tile_spawn.get("name", ""))
                        interval = tile_spawn.get("respawn", tile_spawn.get("interval", 60))
                    elif tile_creature and isinstance(tile_creature, dict):
                        name = tile_creature.get("name", "")
                        interval = tile_creature.get("respawn", 60)
                    if name:
                        spawn_entries.append({
                            "x": self._get_x(tile),
                            "y": self._get_y(tile),
                            "z": self._get_z(tile),
                            "monster_name": name,
                            "interval": int(interval) if interval else 60,
                            "radius": 3,
                        })

            if spawn_entries:
                spawns_buf = io.BytesIO()
                for entry in spawn_entries:
                    monster = self.node.encode_monster(
                        name=entry["monster_name"],
                        direction=2,
                        spawntime=entry["interval"],
                    )
                    spawns_buf.write(
                        self.node.encode_spawn_area(
                            center_x=entry["x"],
                            center_y=entry["y"],
                            center_z=entry["z"],
                            radius=entry["radius"],
                            children=monster,
                        )
                    )
                map_children.write(self.node.encode_spawns(spawns_buf.getvalue()))

            # Towns
            cities = getattr(world_model, "cities", []) or []
            if cities:
                towns_buf = io.BytesIO()
                for idx, city in enumerate(cities, start=1):
                    towns_buf.write(
                        self.node.encode_town(
                            town_id=idx,
                            name=str(self._get_spawn_attr(city, "name", f"Town{idx}")),
                            temple_x=int(self._get_spawn_attr(city, "temple_x", self._get_spawn_attr(city, "x", 0))),
                            temple_y=int(self._get_spawn_attr(city, "temple_y", self._get_spawn_attr(city, "y", 0))),
                            temple_z=int(self._get_spawn_attr(city, "temple_z", self._get_spawn_attr(city, "z", 0))),
                        )
                    )
                map_children.write(self.node.encode_towns(towns_buf.getvalue()))

            # Waypoints
            waypoints = getattr(world_model, "waypoints", []) or []
            if waypoints:
                wp_buf = io.BytesIO()
                for wp in waypoints:
                    wp_buf.write(
                        self.node.encode_waypoint(
                            name=str(self._get_spawn_attr(wp, "name", "waypoint")),
                            x=int(self._get_spawn_attr(wp, "x", 0)),
                            y=int(self._get_spawn_attr(wp, "y", 0)),
                            z=int(self._get_spawn_attr(wp, "z", 0)),
                        )
                    )
                map_children.write(self.node.encode_waypoints(wp_buf.getvalue()))

        # MAP_DATA node
        description = getattr(world_model, "description", "")
        map_data = self.node.encode_map_data(
            description=description,
            spawn_file="",
            house_file="",
            children=map_children.getvalue(),
        )

        # Build final OTBM: magic + ROOT node type + 16-byte root header + MAP_DATA.
        output = io.BytesIO()
        output.write(OTBM_MAGIC)
        output.write(bytes([0x01]))
        output.write(
            struct.pack(
                "<IHHII",
                1,
                max(1, min(0xFFFF, int(width))),
                max(1, min(0xFFFF, int(height))),
                3,
                57,
            )
        )
        output.write(map_data)

        return output.getvalue()

    def _encode_certified_tile_node(self, tile: Any, base_x: int, base_y: int) -> bytes:
        tile_data = self._tile_to_dict(tile)
        x = int(tile_data.get("x", 0))
        y = int(tile_data.get("y", 0))
        offset_x = self._normalize_offset(x - base_x, "tile.offset_x")
        offset_y = self._normalize_offset(y - base_y, "tile.offset_y")
        ground_id = self._resolve_ground(tile_data.get("ground", 106))
        items = tile_data.get("items", []) or []
        flags = tile_data.get("flags", 0)

        children = io.BytesIO()
        children.write(self.node.encode_item(ground_id))
        for item in items:
            item_id = self._resolve_item_id(item)
            count = item.get("count") if isinstance(item, dict) else None
            action_id = item.get("action_id") if isinstance(item, dict) else None
            unique_id = item.get("unique_id") if isinstance(item, dict) else None
            text = item.get("text") if isinstance(item, dict) else None
            children.write(
                self.node.encode_item(
                    item_id,
                    count=count,
                    action_id=action_id,
                    unique_id=unique_id,
                    text=text,
                )
            )

        return self.node.encode_tile(
            offset_x=offset_x,
            offset_y=offset_y,
            tile_flags=flags,
            children=children.getvalue(),
        )

    # ------------------------------------------------------------------
    # v1.0.1 HOTFIX: per-z tile chunking
    # ------------------------------------------------------------------

    def _chunk_tiles(self, tiles: List[Any]) -> List[Tuple[int, int, List[Any]]]:
        if not tiles:
            return []
        buckets: Dict[Tuple[int, int], List[Any]] = {}
        for tile in tiles:
            tx = self._get_x(tile)
            ty = self._get_y(tile)
            bucket = (tx // 256, ty // 256)
            buckets.setdefault(bucket, []).append(tile)

        chunks: List[Tuple[int, int, List[Any]]] = []
        for bucket_tiles in buckets.values():
            base_x = min(self._get_x(tile) for tile in bucket_tiles)
            base_y = min(self._get_y(tile) for tile in bucket_tiles)
            ordered = sorted(bucket_tiles, key=lambda t: (self._get_x(t), self._get_y(t)))
            chunks.append((base_x, base_y, ordered))

        return sorted(chunks, key=lambda chunk: (chunk[0], chunk[1]))

    # ------------------------------------------------------------------
    # Tile encoding
    # ------------------------------------------------------------------

    def _encode_tile_node(self, tile_data: Dict[str, Any],
                          base_x: int = 0, base_y: int = 0) -> bytes:
        x = int(tile_data.get("x", 0))
        y = int(tile_data.get("y", 0))
        offset_x = self._normalize_offset(x - base_x, "tile.offset_x")
        offset_y = self._normalize_offset(y - base_y, "tile.offset_y")
        ground_id = self._resolve_ground(tile_data.get("ground", 106))
        items = tile_data.get("items", []) or []
        flags = tile_data.get("flags", 0)

        children = io.BytesIO()
        _write_item_node(children, item_id=ground_id)
        for item in items:
            item_id = self._resolve_item_id(item)
            count = item.get("count") if isinstance(item, dict) else None
            action_id = item.get("action_id") if isinstance(item, dict) else None
            unique_id = item.get("unique_id") if isinstance(item, dict) else None
            text = item.get("text") if isinstance(item, dict) else None
            _write_item_node(children, item_id=item_id, count=count,
                            action_id=action_id, unique_id=unique_id, text=text)

        tile_buf = io.BytesIO()
        _write_tile_node(tile_buf, offset_x=offset_x, offset_y=offset_y,
                        tile_flags=flags, children=children.getvalue())
        return tile_buf.getvalue()

    # ------------------------------------------------------------------
    # Deserialization (for verification)
    # ------------------------------------------------------------------

    def deserialize(self, data: bytes) -> Dict[str, Any]:
        return self._deserialize_rme(data)

    def _deserialize_rme(self, data: bytes) -> Dict[str, Any]:
        """Read the canonical delimiter tree for serializer roundtrip tests."""
        from .otbm_importer import OTBMAttributeReader, OTBMNodeReader

        with OTBMNodeReader(data) as reader:
            index = reader.build_index(max_nodes=None, max_bytes=None)
            tiles: List[Dict[str, Any]] = []
            for area in index.tile_areas:
                chunk = reader.extract_chunk(
                    area.base_x,
                    area.base_y,
                    area.z,
                    256,
                    256,
                    max_tiles=max(1, area.estimated_tile_count + 1),
                    max_nodes=None,
                    max_bytes=None,
                )
                tiles.extend(chunk["tiles"])

            spawns: List[Dict[str, Any]] = []
            towns: List[Dict[str, Any]] = []
            waypoints: List[Dict[str, Any]] = []
            current_spawn: Dict[str, Any] | None = None

            def on_node(node: Any, _context: Dict[str, Any]) -> None:
                nonlocal current_spawn
                attrs = node.attrs
                if node.node_type == 0x0A and len(attrs) >= 6:
                    current_spawn = {
                        "x": OTBMAttributeReader.u16(attrs, 0),
                        "y": OTBMAttributeReader.u16(attrs, 2),
                        "z": attrs[4],
                        "radius": attrs[5],
                        "monsters": [],
                    }
                    spawns.append(current_spawn)
                elif node.node_type == 0x0B and current_spawn is not None:
                    name, offset = OTBMAttributeReader.string(attrs, 0)
                    current_spawn["monsters"].append({
                        "name": name,
                        "direction": attrs[offset] if offset < len(attrs) else 0,
                        "spawntime": (
                            OTBMAttributeReader.u32(attrs, offset + 1)
                            if offset + 5 <= len(attrs) else 0
                        ),
                    })
                elif node.node_type == 0x0D and len(attrs) >= 6:
                    town_id = OTBMAttributeReader.u32(attrs, 0)
                    name, offset = OTBMAttributeReader.string(attrs, 4)
                    if offset + 5 <= len(attrs):
                        towns.append({
                            "id": town_id,
                            "name": name,
                            "temple_x": OTBMAttributeReader.u16(attrs, offset),
                            "temple_y": OTBMAttributeReader.u16(attrs, offset + 2),
                            "temple_z": attrs[offset + 4],
                        })
                elif node.node_type == 0x10:
                    name, offset = OTBMAttributeReader.string(attrs, 0)
                    if offset + 5 <= len(attrs):
                        waypoints.append({
                            "name": name,
                            "x": OTBMAttributeReader.u16(attrs, offset),
                            "y": OTBMAttributeReader.u16(attrs, offset + 2),
                            "z": attrs[offset + 4],
                        })

            reader.traverse(on_node, max_nodes=None, max_bytes=None)

        metadata = index.metadata
        return {
            "version": metadata.get("version", 0),
            "width": metadata.get("width", 0),
            "height": metadata.get("height", 0),
            "item_version": (
                metadata.get("item_major_version", 0),
                metadata.get("item_minor_version", 0),
            ),
            "tiles": tiles,
            "spawns": spawns,
            "towns": towns,
            "waypoints": waypoints,
            **index.map_attributes,
        }

    def _deserialize_legacy_size_prefixed_stream(self, data: bytes) -> Dict[str, Any]:
        if not data or len(data) < 8:
            raise ValueError(f"Truncated OTBM data: {len(data)} bytes")

        magic = data[:4]
        if magic not in OTBM_ACCEPTED_IDENTIFIERS:
            raise ValueError(f"Invalid OTBM magic: got {magic.hex()}")

        offset = 4
        result: Dict[str, Any] = {
            "tiles": [], "spawns": [], "towns": [], "waypoints": [],
            "version": 0,
        }

        # Read VERSION node
        if data[offset] == NODE_START and data[offset + 1] == 0x00:
            node_type, escaped_size, offset = _read_node_header(data, offset)
            payload, offset = _read_fd_escaped_payload(data, escaped_size, offset)
            if len(payload) >= 4:
                result["version"] = struct.unpack_from("<I", payload, 0)[0]
            # Skip NODE_END
            if offset < len(data) and data[offset] == NODE_END:
                offset += 1

        # Read MAP_DATA node
        if data[offset] == NODE_START and data[offset + 1] == 0x02:
            node_type, escaped_size, offset = _read_node_header(data, offset)
            payload, offset = _read_fd_escaped_payload(data, escaped_size, offset)
            result["description"] = ""
            result["spawn_file"] = ""
            result["house_file"] = ""
            p = 0
            for key in ("description", "spawn_file", "house_file"):
                if p + 2 <= len(payload):
                    slen = struct.unpack_from("<H", payload, p)[0]
                    p += 2
                    s = payload[p:p + slen].decode("utf-8", errors="replace")
                    result[key] = s
                    p += slen
            self._deserialize_nodes(payload, p, result, parent_type=0x02)

        return result

    def _deserialize_nodes(self, data: bytes, offset: int, result: dict,
                           parent_type: int) -> int:
        while offset < len(data):
            if data[offset] == NODE_END:
                return offset + 1
            if data[offset] != NODE_START:
                offset += 1
                continue
            offset = self._deserialize_node(data, offset, result, parent_type)
        return offset

    def _deserialize_node(self, data: bytes, offset: int, result: dict,
                          parent_type: int) -> int:
        node_type, escaped_size, offset = _read_node_header(data, offset)
        payload, offset = _read_fd_escaped_payload(data, escaped_size, offset)
        payload_offset = 0

        if node_type == 0x04:  # TILE_AREA
            if len(payload) < 5:
                return offset
            base_x = struct.unpack_from("<H", payload, payload_offset)[0]
            payload_offset += 2
            base_y = struct.unpack_from("<H", payload, payload_offset)[0]
            payload_offset += 2
            base_z = payload[payload_offset]
            payload_offset += 1
            while payload_offset < len(payload):
                ct, cs, co = _read_node_header(payload, payload_offset)
                cp, co = _read_fd_escaped_payload(payload, cs, co)
                if ct == 0x05:
                    self._deserialize_tile(cp, base_x, base_y, base_z, result)
                payload_offset = co
                while payload_offset < len(payload) and payload[payload_offset] != NODE_END:
                    payload_offset += 1
                if payload_offset < len(payload):
                    payload_offset += 1

        elif node_type == 0x09:  # SPAWNS
            self._deserialize_nodes(payload, payload_offset, result, 0x09)

        elif node_type == 0x0A:  # SPAWN_AREA
            if len(payload) < 6:
                return offset
            cx = struct.unpack_from("<H", payload, payload_offset)[0]
            payload_offset += 2
            cy = struct.unpack_from("<H", payload, payload_offset)[0]
            payload_offset += 2
            cz = payload[payload_offset]
            payload_offset += 1
            radius = payload[payload_offset]
            payload_offset += 1
            spawn_entry = {"center_x": cx, "center_y": cy, "center_z": cz,
                          "radius": radius, "monsters": []}
            while payload_offset < len(payload):
                mt, ms, mo = _read_node_header(payload, payload_offset)
                mp, mo = _read_fd_escaped_payload(payload, ms, mo)
                if mt == 0x0B:
                    name, mp2 = self._read_string_fd(mp, 0)
                    direction = mp[mp2]
                    spawntime = struct.unpack_from("<I", mp, mp2 + 1)[0]
                    spawn_entry["monsters"].append({
                        "name": name, "direction": direction, "spawntime": spawntime
                    })
                payload_offset = mo
                while payload_offset < len(payload) and payload[payload_offset] != NODE_END:
                    payload_offset += 1
                if payload_offset < len(payload):
                    payload_offset += 1
            result["spawns"].append(spawn_entry)

        elif node_type == 0x0C:  # TOWNS
            while payload_offset < len(payload):
                tt, ts, to = _read_node_header(payload, payload_offset)
                tp, to = _read_fd_escaped_payload(payload, ts, to)
                if tt == 0x0D and len(tp) >= 8:
                    tid = struct.unpack_from("<I", tp, 0)[0]
                    name, tp2 = self._read_string_fd(tp, 4)
                    tx = struct.unpack_from("<H", tp, tp2)[0]
                    tp2 += 2
                    ty = struct.unpack_from("<H", tp, tp2)[0]
                    tp2 += 2
                    tz = tp[tp2]
                    result["towns"].append({
                        "town_id": tid, "name": name,
                        "temple_x": tx, "temple_y": ty, "temple_z": tz
                    })
                payload_offset = to
                while payload_offset < len(payload) and payload[payload_offset] != NODE_END:
                    payload_offset += 1
                if payload_offset < len(payload):
                    payload_offset += 1

        elif node_type == 0x0F:  # WAYPOINTS
            while payload_offset < len(payload):
                wt, ws, wo = _read_node_header(payload, payload_offset)
                wp, wo = _read_fd_escaped_payload(payload, ws, wo)
                if wt == 0x10:
                    name, wp2 = self._read_string_fd(wp, 0)
                    wx = struct.unpack_from("<H", wp, wp2)[0]
                    wp2 += 2
                    wy = struct.unpack_from("<H", wp, wp2)[0]
                    wp2 += 2
                    wz = wp[wp2]
                    result["waypoints"].append({
                        "name": name, "x": wx, "y": wy, "z": wz
                    })
                payload_offset = wo
                while payload_offset < len(payload) and payload[payload_offset] != NODE_END:
                    payload_offset += 1
                if payload_offset < len(payload):
                    payload_offset += 1

        return offset

    def _deserialize_tile(self, payload: bytes, base_x: int, base_y: int,
                          base_z: int, result: dict) -> None:
        if len(payload) < 2:
            return
        offset = 0
        off_x = payload[offset]
        offset += 1
        off_y = payload[offset]
        offset += 1
        abs_x = base_x + off_x
        abs_y = base_y + off_y
        flags = 0
        if offset < len(payload) and payload[offset] == ATTR_TILE_FLAGS:
            offset += 1
            if offset + 4 <= len(payload):
                flags = struct.unpack_from("<I", payload, offset)[0]
                offset += 4
        items = []
        while offset < len(payload):
            if payload[offset] == NODE_START:
                it, isize, ioffset = _read_node_header(payload, offset)
                if it == 0x06:
                    ip, _ = _read_fd_escaped_payload(payload, isize, ioffset)
                    items.append(self._deserialize_item_payload(ip))
                offset = ioffset + isize
                while offset < len(payload) and payload[offset] != NODE_END:
                    offset += 1
                if offset < len(payload):
                    offset += 1
            else:
                offset += 1
        result["tiles"].append({
            "x": abs_x, "y": abs_y, "z": base_z, "flags": flags, "items": items
        })

    def _deserialize_item_payload(self, payload: bytes) -> Dict[str, Any]:
        if len(payload) < 2:
            return {"id": 0}
        offset = 0
        item_id = struct.unpack_from("<H", payload, offset)[0]
        offset += 2
        item: Dict[str, Any] = {"id": item_id}
        while offset < len(payload):
            attr = payload[offset]
            offset += 1
            if attr in (ATTR_COUNT, ATTR_SUBTYPE, ATTR_CHARGES):
                if offset < len(payload):
                    key = "count" if attr == ATTR_COUNT else ("subtype" if attr == ATTR_SUBTYPE else "charges")
                    item[key] = payload[offset]
                    offset += 1
            elif attr in (ATTR_ACTION_ID, ATTR_UNIQUE_ID):
                if offset + 2 <= len(payload):
                    key = "action_id" if attr == ATTR_ACTION_ID else "unique_id"
                    item[key] = struct.unpack_from("<H", payload, offset)[0]
                    offset += 2
            elif attr == ATTR_TEXT:
                text, offset = self._read_string_fd(payload, offset)
                item["text"] = text
            elif attr == ATTR_DURATION:
                if offset + 4 <= len(payload):
                    item["duration"] = struct.unpack_from("<I", payload, offset)[0]
                    offset += 4
            elif attr == ATTR_DECAYING_STATE:
                if offset < len(payload):
                    item["decaying_state"] = payload[offset]
                    offset += 1
            else:
                break
        return item

    @staticmethod
    def _read_string_fd(data: bytes, offset: int) -> Tuple[str, int]:
        if offset + 2 > len(data):
            return "", offset
        length = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        if offset + length > len(data):
            length = len(data) - offset
        text = data[offset:offset + length].decode("utf-8", errors="replace")
        return text, offset + length

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tile_to_dict(tile: Any) -> Dict[str, Any]:
        if isinstance(tile, dict):
            return tile
        if hasattr(tile, "to_dict"):
            return cast(Dict[str, Any], tile.to_dict())
        return {
            "x": getattr(tile, "x", 0),
            "y": getattr(tile, "y", 0),
            "z": getattr(tile, "z", 0),
            "ground": getattr(tile, "ground", 106),
            "items": getattr(tile, "items", []),
            "spawn": getattr(tile, "spawn", None),
            "creature": getattr(tile, "creature", None),
            "flags": getattr(tile, "flags", 0),
        }

    @staticmethod
    def _get_x(tile: Any) -> int:
        if isinstance(tile, dict):
            return int(tile.get("x", 0))
        return int(getattr(tile, "x", 0))

    @staticmethod
    def _get_y(tile: Any) -> int:
        if isinstance(tile, dict):
            return int(tile.get("y", 0))
        return int(getattr(tile, "y", 0))

    @staticmethod
    def _get_z(tile: Any) -> int:
        if isinstance(tile, dict):
            return int(tile.get("z", 0))
        return int(getattr(tile, "z", 0))

    @staticmethod
    def _get_spawn(tile: Any) -> Optional[Dict]:
        if isinstance(tile, dict):
            return tile.get("spawn")
        return getattr(tile, "spawn", None)

    @staticmethod
    def _get_creature(tile: Any) -> Optional[Dict]:
        if isinstance(tile, dict):
            return tile.get("creature")
        return getattr(tile, "creature", None)

    @staticmethod
    def _get_spawn_name(spawn: Dict) -> str:
        if isinstance(spawn, dict):
            return str(spawn.get("monster", "") or spawn.get("name", "") or spawn.get("creature", ""))
        return str(
            getattr(spawn, "monster", "")
            or getattr(spawn, "name", "")
            or getattr(spawn, "creature", "")
        )

    @staticmethod
    def _get_spawn_attr(spawn: Any, name: str, default: Any = None) -> Any:
        if isinstance(spawn, dict):
            return spawn.get(name, default)
        return getattr(spawn, name, default)

    @staticmethod
    def _get_optional_int(obj: Any, name: str) -> Optional[int]:
        raw = obj.get(name) if isinstance(obj, dict) else getattr(obj, name, None)
        if raw is None:
            return None
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return None
        if value <= 0:
            return None
        return value

    @staticmethod
    def _normalize_offset(value: Any, context: str) -> int:
        try:
            iv = int(value) if value is not None else 0
        except (TypeError, ValueError):
            return 0
        if iv < 0 or iv > 255:
            clamped = max(0, min(255, iv))
            return clamped
        return iv

    @staticmethod
    def _resolve_ground(ground_value: Any) -> int:
        try:
            return int(ground_value)
        except (TypeError, ValueError):
            pass
        if isinstance(ground_value, str):
            lower = ground_value.lower().replace(" ", "_").replace("-", "_")
            from .tile_encoder import GROUND_IDS
            if lower in GROUND_IDS:
                return GROUND_IDS[lower]
            for key, val in GROUND_IDS.items():
                if key in lower or lower in key:
                    return val
        return 106

    @staticmethod
    def _resolve_item_id(item: Any) -> int:
        if isinstance(item, (int, float)):
            return int(item)
        if isinstance(item, dict):
            if "id" in item:
                try:
                    return int(item["id"])
                except (TypeError, ValueError):
                    pass
            return 0
        if isinstance(item, str):
            from .tile_encoder import WALL_IDS, DECORATION_IDS, GROUND_IDS
            lower = item.lower().replace(" ", "_").replace("-", "_")
            for d in (WALL_IDS, DECORATION_IDS, GROUND_IDS):
                for key, val in d.items():
                    if key in lower or lower in key:
                        return val
        return 0

    def serialize_hunt_area(self, hunt_area, spawn_plan=None) -> bytes:
        tiles_raw = self._get_attr(hunt_area, "tiles", {})
        if isinstance(tiles_raw, dict):
            tiles_list = list(tiles_raw.values())
        else:
            tiles_list = list(tiles_raw)
        spawns_raw = self._get_attr(hunt_area, "spawns", []) or []

        base_x_val = self._get_attr(hunt_area, "base_x", 1000)
        base_y_val = self._get_attr(hunt_area, "base_y", 1000)
        base_z_val = self._get_attr(hunt_area, "base_z", 7)

        all_x, all_y = [], []
        for t in tiles_list:
            tx = self._get_attr(t, "x", base_x_val)
            ty = self._get_attr(t, "y", base_y_val)
            all_x.append(tx)
            all_y.append(ty)

        if not all_x:
            all_x = [base_x_val]
            all_y = [base_y_val]

        width = max(all_x) - min(all_x) + 1
        height = max(all_y) - min(all_y) + 1
        base_x = min(all_x)
        base_y = min(all_y)
        base_z = base_z_val

        map_children = io.BytesIO()
        tile_nodes = io.BytesIO()
        for tile in tiles_list:
            tile_dict = {
                "x": self._get_attr(tile, "x", base_x),
                "y": self._get_attr(tile, "y", base_y),
                "z": self._get_attr(tile, "z", base_z),
                "ground": self._get_attr(tile, "ground", 106),
                "items": self._get_attr(tile, "items", []),
                "flags": self._get_attr(tile, "flags", 0),
            }
            tile_bytes = self._encode_tile_node(tile_dict, base_x=base_x, base_y=base_y)
            tile_nodes.write(tile_bytes)

        tile_area_buf = io.BytesIO()
        _write_tile_area_node(tile_area_buf,
                              base_x=base_x, base_y=base_y, base_z=base_z,
                              children=tile_nodes.getvalue())
        map_children.write(tile_area_buf.getvalue())

        spawn_entries: List[Dict[str, Any]] = []
        for s in spawns_raw:
            if len(s) >= 3:
                spawn_entries.append({
                    "x": s[0], "y": s[1],
                    "monster_name": s[2],
                    "interval": s[3] if len(s) > 3 else 60,
                    "radius": 3,
                })

        if spawn_plan:
            for entry in getattr(spawn_plan, "spawns", []):
                spawn_entries.append({
                    "x": entry.x, "y": entry.y,
                    "z": getattr(entry, "z", base_z),
                    "monster_name": entry.monster_name,
                    "interval": getattr(entry, "interval", 60),
                    "radius": 3,
                })
            boss = getattr(spawn_plan, "boss_spawn", None)
            if boss:
                spawn_entries.append({
                    "x": boss.x, "y": boss.y,
                    "z": getattr(boss, "z", base_z),
                    "monster_name": boss.monster_name,
                    "interval": getattr(boss, "interval", 600),
                    "radius": 3,
                })

        if spawn_entries:
            spawns_buf = io.BytesIO()
            for entry in spawn_entries:
                monster_buf = io.BytesIO()
                _write_monster_node(monster_buf, name=entry["monster_name"],
                                    direction=2, spawntime=entry["interval"])
                _write_spawn_area_node(spawns_buf,
                                      center_x=int(entry.get("x", base_x)),
                                      center_y=int(entry.get("y", base_y)),
                                      center_z=int(entry.get("z", base_z)),
                                      radius=entry["radius"],
                                      children=monster_buf.getvalue())
            spawns_node = io.BytesIO()
            _write_spawns_node(spawns_node, children=spawns_buf.getvalue())
            map_children.write(spawns_node.getvalue())

        map_data_buf = io.BytesIO()
        _write_map_data_node(map_data_buf,
                             description="Generated by OpenTibiaBR RME Agent \u2014 Hunt Area",
                             spawn_file="",
                             house_file="",
                             children=map_children.getvalue())

        output = io.BytesIO()
        output.write(OTBM_MAGIC)
        _write_root_node(output, width=width, height=height, children=map_data_buf.getvalue())

        return output.getvalue()

    def _get_attr(self, obj, name, default=None):
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)


# ====================================================================
# Node reader helpers
# ====================================================================

def _read_node_header(data: bytes, offset: int) -> Tuple[int, int, int]:
    """Read node header: FE [type] [size]"""
    if offset >= len(data) or data[offset] != NODE_START:
        raise ValueError(f"Expected NODE_START at offset {offset}")
    node_type = data[offset + 1]
    offset += 2
    # VERSION node uses uint32, all others use uint16
    if node_type == 0x00:
        size = struct.unpack_from("<I", data, offset)[0]
        offset += 4
    else:
        size = struct.unpack_from("<H", data, offset)[0]
        offset += 2
    return node_type, size, offset


def _read_fd_escaped_payload(data: bytes, escaped_size: int, offset: int) -> Tuple[bytes, int]:
    if offset + escaped_size > len(data):
        raise ValueError(f"Truncated payload: need {escaped_size}, have {len(data) - offset}")
    escaped = data[offset:offset + escaped_size]
    unescaped, _ = _fd_unescape(escaped, 0)
    return unescaped, offset + escaped_size
