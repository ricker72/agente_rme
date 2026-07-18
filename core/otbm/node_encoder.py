from __future__ import annotations

import io
import struct
import logging
from typing import Optional

from .binary_writer import BinaryWriter
from .compatibility.otbm_constants import (
    OTBM_ROOTV1,
    OTBM_MAP_DATA,
    OTBM_TILE_AREA,
    OTBM_TILE,
    OTBM_ITEM,
    OTBM_SPAWNS,
    OTBM_SPAWN_AREA,
    OTBM_MONSTER,
    OTBM_TOWNS,
    OTBM_TOWN,
    OTBM_HOUSETILE,
    OTBM_WAYPOINTS,
    OTBM_WAYPOINT,
    OTBM_ATTR_DESCRIPTION,
    OTBM_ATTR_EXT_FILE,
    OTBM_ATTR_EXT_HOUSE_FILE,
    OTBM_ATTR_TILE_FLAGS,
    OTBM_ATTR_ITEM,
    OTBM_ATTR_COUNT,
    OTBM_ATTR_ACTION_ID,
    OTBM_ATTR_UNIQUE_ID,
    OTBM_ATTR_TEXT,
    OTBM_ATTR_DESC,
    OTBM_ATTR_EXT_SPAWN_MONSTER_FILE,
    OTBM_ATTR_CHARGES,
    OTBM_ATTR_DURATION,
    OTBM_ATTR_DECAYING_STATE,
    OTBM_ATTR_WRITTENDATE,
    OTBM_ATTR_WRITTENBY,
    OTBM_ATTR_SLEEPERGUID,
    OTBM_ATTR_SLEEPSTART,
    OTBM_ATTR_SUBTYPE,
    DEFAULT_OTBM_VERSION,
    DEFAULT_ITEM_MAJOR_VERSION,
    DEFAULT_ITEM_MINOR_VERSION,
)

logger = logging.getLogger(__name__)

# ============================================================
# OTBM Binary Format Node Types (OpenTibia Binary Map)
# These are the node type identifiers used in .otbm files
# ============================================================

# Map header nodes. These public aliases intentionally point to the
# canonical Canary/RME constants; legacy Agente values live only in
# compatibility.otbm_constants for migration detection tests.
OTBM_NODE_ROOT = 0x00
OTBM_NODE_MAP_DATA = OTBM_MAP_DATA
OTBM_NODE_TILE_AREA = OTBM_TILE_AREA
OTBM_NODE_TILE = OTBM_TILE
OTBM_NODE_ITEM = OTBM_ITEM
OTBM_NODE_TILE_SQUARE = 0x07  # deprecated / unused in modern TFS
OTBM_NODE_SPAWNS = OTBM_SPAWNS
OTBM_NODE_SPAWN_AREA = OTBM_SPAWN_AREA
OTBM_NODE_MONSTER = OTBM_MONSTER
OTBM_NODE_TOWNS = OTBM_TOWNS
OTBM_NODE_TOWN = OTBM_TOWN
OTBM_NODE_HOUSETILE = OTBM_HOUSETILE
OTBM_NODE_WAYPOINTS = OTBM_WAYPOINTS
OTBM_NODE_WAYPOINT = OTBM_WAYPOINT

# Attribute types (used inside item nodes)
ATTR_DESCRIPTION = OTBM_ATTR_DESCRIPTION
ATTR_EXT_HOUSE_FILE = OTBM_ATTR_EXT_HOUSE_FILE
ATTR_EXT_SPAWN_FILE = OTBM_ATTR_EXT_SPAWN_MONSTER_FILE
ATTR_TILE_FLAGS = OTBM_ATTR_TILE_FLAGS
ATTR_ITEM = OTBM_ATTR_ITEM
ATTR_COUNT = OTBM_ATTR_COUNT
ATTR_ACTION_ID = OTBM_ATTR_ACTION_ID
ATTR_UNIQUE_ID = OTBM_ATTR_UNIQUE_ID
ATTR_TEXT = OTBM_ATTR_TEXT
ATTR_DESC = OTBM_ATTR_DESC
ATTR_EXT_FILE = OTBM_ATTR_EXT_FILE
ATTR_DURATION = OTBM_ATTR_DURATION
ATTR_DECAYING_STATE = OTBM_ATTR_DECAYING_STATE
ATTR_WRITTEN_DATE = OTBM_ATTR_WRITTENDATE
ATTR_WRITTEN_BY = OTBM_ATTR_WRITTENBY
ATTR_SLEEPERGUID = OTBM_ATTR_SLEEPERGUID
ATTR_SLEEPSTART = OTBM_ATTR_SLEEPSTART
ATTR_CHARGES = OTBM_ATTR_CHARGES
ATTR_SUBTYPE = OTBM_ATTR_SUBTYPE

# Tile flags (bitmask)
TILESTATE_NONE = 0x0000
TILESTATE_PROTECTIONZONE = 0x0001
TILESTATE_NOPVPZONE = 0x0004
TILESTATE_NOLOGOUT = 0x0008
TILESTATE_PVPZONE = 0x0010
TILESTATE_REFRESH = 0x0020
TILESTATE_TRASHED = 0x0040

# Map header constants
OTBM_IDENTIFIER = b"\x00\x00\x00\x00"  # Canonical Canary/RME identifier
DEFAULT_OTBM_VERSION = DEFAULT_OTBM_VERSION
DEFAULT_ITEM_MAJOR_VERSION = DEFAULT_ITEM_MAJOR_VERSION
DEFAULT_ITEM_MINOR_VERSION = DEFAULT_ITEM_MINOR_VERSION


class NodeEncoder:
    """
    Low-level encoder for OTBM binary nodes.

    Each node has:
      [1 byte: node_type]
      [2 bytes: attribute + children size]  (in RME, this was uint16)
      If node_type == ROOT:
        [4 bytes: OTBM version (uint32)]
        [2 bytes: header size (uint16)]
      Attributes (variable length)
      Children nodes (variable length)

    For non-root nodes:
      [1 byte: node_type]
      [2 bytes: children size]   -- only counts children, not own attrs
      [attributes for this node]
      [children...]

    Actually the real binary format is slightly different in different versions.
    We implement the version used by RME (Remere's Map Editor) which is:
      Root: [type:1] [size:4] [attrs+children]
      Map/TileArea/Tile/Item: [type:1] [size:2] [attrs+children]
    """

    def __init__(self):
        self._buffer = io.BytesIO()
        self._indent = 0
        # Every encoder shares a single BinaryWriter so that range
        # validation is consistent across the whole export pipeline.
        self._bw = BinaryWriter()

    # ------------------------------------------------------------------
    # Node construction
    # ------------------------------------------------------------------

    def encode_root(
        self,
        otbm_version: int,
        width: int,
        height: int,
        item_major: int,
        item_minor: int,
        children: bytes,
    ) -> bytes:
        """Build the root node for an OTBM file."""
        buf = io.BytesIO()
        self._bw.write_u32(buf, otbm_version, context="root.otbm_version")
        self._bw.write_u16(buf, width, context="root.width")
        self._bw.write_u16(buf, height, context="root.height")
        self._bw.write_u32(buf, item_major, context="root.item_major")
        self._bw.write_u32(buf, item_minor, context="root.item_minor")
        return self._wrap_node(OTBM_NODE_ROOT, buf.getvalue(), children)

    def encode_map_data(
        self,
        description: str = "",
        spawn_file: str = "",
        house_file: str = "",
        children: bytes = b"",
    ) -> bytes:
        """Build a MAP_DATA node containing metadata."""
        buf = io.BytesIO()
        if description:
            self._bw.write_u8(buf, OTBM_ATTR_DESCRIPTION)
            self._bw.write_string(buf, description)
        if spawn_file:
            self._bw.write_u8(buf, OTBM_ATTR_EXT_SPAWN_MONSTER_FILE)
            self._bw.write_string(buf, spawn_file)
        if house_file:
            self._bw.write_u8(buf, OTBM_ATTR_EXT_HOUSE_FILE)
            self._bw.write_string(buf, house_file)
        return self._wrap_node(OTBM_MAP_DATA, buf.getvalue(), children)

    def encode_tile_area(self, base_x: int, base_y: int, base_z: int, children: bytes) -> bytes:
        """Build a TILE_AREA node."""
        buf = io.BytesIO()
        self._bw.write_u16(buf, base_x, context="tile_area.base_x")
        self._bw.write_u16(buf, base_y, context="tile_area.base_y")
        self._bw.write_u8(buf, base_z, context="tile_area.base_z")
        return self._wrap_node(OTBM_TILE_AREA, buf.getvalue(), children)

    def encode_tile(
        self,
        offset_x: int,
        offset_y: int,
        tile_flags: int = 0,
        children: bytes = b"",
    ) -> bytes:
        """
        Build a TILE node.

        offset_x, offset_y are relative to the TILE_AREA base.
        tile_flags encodes PZ, protection, etc.
        children are ITEM nodes.
        """
        buf = io.BytesIO()
        self._bw.write_u8(buf, offset_x, context="tile.offset_x")
        self._bw.write_u8(buf, offset_y, context="tile.offset_y")
        if tile_flags:
            self._bw.write_u8(buf, OTBM_ATTR_TILE_FLAGS, context="tile.flags_attr")
            self._bw.write_u32(buf, tile_flags, context="tile.flags_value")
        return self._wrap_node(OTBM_TILE, buf.getvalue(), children)

    def encode_item(
        self,
        item_id: int,
        count: Optional[int] = None,
        action_id: Optional[int] = None,
        unique_id: Optional[int] = None,
        text: Optional[str] = None,
        subtype: Optional[int] = None,
        charges: Optional[int] = None,
        duration: Optional[int] = None,
        decaying_state: Optional[int] = None,
        children: bytes = b"",
    ) -> bytes:
        """
        Build an ITEM node.

        Children are nested items (e.g. items inside a container).
        """
        buf = io.BytesIO()
        self._bw.write_u16(buf, item_id, context="item.id")
        if count is not None:
            self._bw.write_u8(buf, OTBM_ATTR_COUNT, context="item.count_attr")
            self._bw.write_u8(buf, count, context="item.count")
        if action_id is not None:
            self._bw.write_u8(buf, OTBM_ATTR_ACTION_ID, context="item.action_id_attr")
            self._bw.write_u16(buf, action_id, context="item.action_id")
        if unique_id is not None:
            self._bw.write_u8(buf, OTBM_ATTR_UNIQUE_ID, context="item.unique_id_attr")
            self._bw.write_u16(buf, unique_id, context="item.unique_id")
        if text is not None:
            self._bw.write_u8(buf, OTBM_ATTR_TEXT, context="item.text_attr")
            self._bw.write_string(buf, text)
        if subtype is not None:
            self._bw.write_u8(buf, OTBM_ATTR_SUBTYPE, context="item.subtype_attr")
            self._bw.write_u8(buf, subtype, context="item.subtype")
        if charges is not None:
            self._bw.write_u8(buf, OTBM_ATTR_CHARGES, context="item.charges_attr")
            self._bw.write_u8(buf, charges, context="item.charges")
        if duration is not None:
            self._bw.write_u8(buf, OTBM_ATTR_DURATION, context="item.duration_attr")
            self._bw.write_u32(buf, duration, context="item.duration")
        if decaying_state is not None:
            self._bw.write_u8(buf, OTBM_ATTR_DECAYING_STATE, context="item.decaying_state_attr")
            self._bw.write_u8(buf, decaying_state, context="item.decaying_state")
        return self._wrap_node(OTBM_ITEM, buf.getvalue(), children)

    def encode_house_tile(
        self,
        offset_x: int,
        offset_y: int,
        house_id: int,
        children: bytes = b"",
    ) -> bytes:
        """Build a HOUSETILE node."""
        buf = io.BytesIO()
        self._bw.write_u8(buf, offset_x, context="house_tile.offset_x")
        self._bw.write_u8(buf, offset_y, context="house_tile.offset_y")
        self._bw.write_u32(buf, house_id, context="house_tile.house_id")
        return self._wrap_node(OTBM_HOUSETILE, buf.getvalue(), children)

    # ------------------------------------------------------------------
    # Spawn nodes
    # ------------------------------------------------------------------

    def encode_spawns(self, children: bytes) -> bytes:
        """Build a SPAWNS container node."""
        return self._wrap_node(OTBM_SPAWNS, b"", children)

    def encode_spawn_area(
        self, center_x: int, center_y: int, center_z: int, radius: int, children: bytes
    ) -> bytes:
        """Build a SPAWN_AREA node."""
        buf = io.BytesIO()
        self._bw.write_u16(buf, center_x, context="spawn_area.center_x")
        self._bw.write_u16(buf, center_y, context="spawn_area.center_y")
        self._bw.write_u8(buf, center_z, context="spawn_area.center_z")
        self._bw.write_u8(buf, radius, context="spawn_area.radius")
        return self._wrap_node(OTBM_SPAWN_AREA, buf.getvalue(), children)

    def encode_monster(self, name: str, direction: int = 2, spawntime: int = 60) -> bytes:
        """Build a MONSTER node (inside SPAWN_AREA)."""
        buf = io.BytesIO()
        self._bw.write_string(buf, name)
        self._bw.write_u8(buf, direction, context="monster.direction")  # 0=N, 1=E, 2=S, 3=W
        self._bw.write_u32(buf, spawntime, context="monster.spawntime")
        return self._wrap_node(OTBM_MONSTER, buf.getvalue())

    # ------------------------------------------------------------------
    # Town nodes
    # ------------------------------------------------------------------

    def encode_towns(self, children: bytes) -> bytes:
        """Build a TOWNS container node."""
        return self._wrap_node(OTBM_TOWNS, b"", children)

    def encode_town(
        self, town_id: int, name: str, temple_x: int, temple_y: int, temple_z: int
    ) -> bytes:
        """Build a TOWN node."""
        buf = io.BytesIO()
        self._bw.write_u32(buf, town_id, context="town.town_id")
        self._bw.write_string(buf, name)
        self._bw.write_u16(buf, temple_x, context="town.temple_x")
        self._bw.write_u16(buf, temple_y, context="town.temple_y")
        self._bw.write_u8(buf, temple_z, context="town.temple_z")
        return self._wrap_node(OTBM_TOWN, buf.getvalue())

    # ------------------------------------------------------------------
    # Waypoint nodes
    # ------------------------------------------------------------------

    def encode_waypoints(self, children: bytes) -> bytes:
        """Build a WAYPOINTS container node."""
        return self._wrap_node(OTBM_WAYPOINTS, b"", children)

    def encode_waypoint(self, name: str, x: int, y: int, z: int) -> bytes:
        """Build a WAYPOINT node."""
        buf = io.BytesIO()
        self._bw.write_string(buf, name)
        self._bw.write_u16(buf, x, context="waypoint.x")
        self._bw.write_u16(buf, y, context="waypoint.y")
        self._bw.write_u8(buf, z, context="waypoint.z")
        return self._wrap_node(OTBM_WAYPOINT, buf.getvalue())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _wrap_node(node_type: int, attrs: bytes, children: bytes = b"") -> bytes:
        """Wrap attributes and literal child nodes in the RME delimiter stream."""
        bw = BinaryWriter()
        bw.validate_u8(node_type, context="wrap_node.node_type")
        payload = bytes((node_type,)) + attrs
        escaped = bytearray()
        for byte in payload:
            if byte in (0xFD, 0xFE, 0xFF):
                escaped.append(0xFD)
            escaped.append(byte)
        return b"\xFE" + bytes(escaped) + children + b"\xFF"

    @staticmethod
    def _write_uint8(buf: io.BytesIO, value: int) -> None:
        """Backwards-compatible helper. Prefer ``BinaryWriter.write_u8``."""
        BinaryWriter().write_u8(buf, value)

    @staticmethod
    def _write_uint16(buf: io.BytesIO, value: int) -> None:
        """Backwards-compatible helper. Prefer ``BinaryWriter.write_u16``."""
        BinaryWriter().write_u16(buf, value)

    @staticmethod
    def _write_uint32(buf: io.BytesIO, value: int) -> None:
        """Backwards-compatible helper. Prefer ``BinaryWriter.write_u32``."""
        BinaryWriter().write_u32(buf, value)

    @staticmethod
    def _write_string(buf: io.BytesIO, text: str) -> None:
        """Backwards-compatible helper. Prefer ``BinaryWriter.write_string``."""
        BinaryWriter().write_string(buf, text)

    # ------------------------------------------------------------------
    # Reading helpers (for deserialization)
    # ------------------------------------------------------------------

    @staticmethod
    def read_uint8(data: bytes, offset: int) -> tuple:
        """Return (value, new_offset)."""
        return data[offset], offset + 1

    @staticmethod
    def read_uint16(data: bytes, offset: int) -> tuple:
        return struct.unpack_from("<H", data, offset)[0], offset + 2

    @staticmethod
    def read_uint32(data: bytes, offset: int) -> tuple:
        return struct.unpack_from("<I", data, offset)[0], offset + 4

    @staticmethod
    def read_string(data: bytes, offset: int) -> tuple:
        length, offset = struct.unpack_from("<H", data, offset)[0], offset + 2
        text = data[offset : offset + length].decode("utf-8", errors="ignore")
        return text, offset + length

    @staticmethod
    def read_node_header(data: bytes, offset: int) -> tuple:
        """Return (node_type, size, new_offset)."""
        if offset + 3 > len(data):
            raise ValueError("Truncated node header")
        node_type = data[offset]
        size = struct.unpack_from("<H", data, offset + 1)[0]
        return node_type, size, offset + 3
