"""
OTBM Parser — Low-level parser for OTBM binary node structures.

Parses the raw binary tree structure:
    ROOT -> MAP_DATA -> TILE_AREA -> TILE -> ITEM
                     -> SPAWNS -> SPAWN_AREA -> MONSTER
                     -> TOWNS -> TOWN
                     -> WAYPOINTS -> WAYPOINT

Returns raw node tuples: (node_type, size, payload, children)
for higher-level decoders to process.
"""

from __future__ import annotations

import struct
from typing import Any, Dict, List, Optional, Tuple

from .node_encoder import (
    NodeEncoder,
    OTBM_NODE_ROOT,
    OTBM_NODE_MAP_DATA,
    OTBM_NODE_TILE_AREA,
    OTBM_NODE_TILE,
    OTBM_NODE_ITEM,
    OTBM_NODE_TILE_SQUARE,
    OTBM_NODE_SPAWNS,
    OTBM_NODE_SPAWN_AREA,
    OTBM_NODE_TOWNS,
    OTBM_NODE_HOUSETILE,
    OTBM_NODE_WAYPOINTS,
)

# OTBM magic bytes
OTBM_MAGIC = b"OTBM"


class OtbmParseError(Exception):
    """Raised when OTBM binary data is malformed."""


class OtbmParser:
    """
    Parses OTBM binary data into a tree of raw nodes.

    Handles the real OTBM binary format where:
      - Root node: [type:1] [version:4] [width:2] [height:2]
                   [item_major:4] [item_minor:4] [children...]
      - Standard nodes: [type:1] [size:2] [payload:size] where
        payload CAN contain child nodes embedded within.
      - MAP_DATA: payload = [desc_str] [spawn_str] [house_str] [children...]
      - TILE: payload = [offset_x:1] [offset_y:1] [opt attrs] [children ITEM nodes...]
      - ITEM: payload = [item_id:2] [opt attrs] [children ITEM nodes...]
      - MONSTER/TOWN/WAYPOINT: leaf nodes with no children
    """

    # Node types that contain child nodes
    CONTAINER_NODES = {
        OTBM_NODE_MAP_DATA,
        OTBM_NODE_TILE_AREA,
        OTBM_NODE_SPAWNS,
        OTBM_NODE_SPAWN_AREA,
        OTBM_NODE_TOWNS,
        OTBM_NODE_WAYPOINTS,
    }

    # Node types for tiles (may contain ITEM children)
    TILE_NODES = {OTBM_NODE_TILE, OTBM_NODE_HOUSETILE, OTBM_NODE_TILE_SQUARE}

    def __init__(self):
        self._node_encoder = NodeEncoder()

    def parse(self, data: bytes) -> Dict[str, Any]:
        """
        Parse OTBM binary data into a structured tree.

        Args:
            data: Raw .otbm file bytes (including "OTBM" magic).

        Returns:
            dict with structure:
            {
                "magic": "OTBM",
                "root": {
                    "type": OTBM_NODE_ROOT,
                    "version": int,
                    "width": int,
                    "height": int,
                    "item_major": int,
                    "item_minor": int,
                    "children": [ ... node dicts ... ]
                }
            }
        """
        if data[:4] != OTBM_MAGIC:
            raise OtbmParseError(
                f"Invalid OTBM magic: {data[:4]!r}, expected {OTBM_MAGIC!r}"
            )

        offset = 4  # Skip magic
        root_node, _ = self._parse_node(data, offset)
        return {
            "magic": "OTBM",
            "root": root_node,
        }

    # ------------------------------------------------------------------
    # Node parsing
    # ------------------------------------------------------------------

    def _parse_node(self, data: bytes, offset: int) -> Tuple[Dict[str, Any], int]:
        """
        Parse a single node from binary data at given offset.

        Returns:
            (node_dict, new_offset)
        """
        if offset >= len(data):
            raise OtbmParseError(f"Unexpected end of data at offset {offset}")

        node_type = data[offset]
        offset += 1

        if node_type == OTBM_NODE_ROOT:
            return self._parse_root(data, offset)
        else:
            return self._parse_standard_node(data, offset, node_type)

    def _parse_root(self, data: bytes, offset: int) -> Tuple[Dict[str, Any], int]:
        """
        Parse ROOT node. Root does NOT have a size prefix.

        ROOT structure:
            [type: 1] [version: 4] [width: 2] [height: 2]
            [item_major: 4] [item_minor: 4] [children...]
        """
        if offset + 16 > len(data):
            raise OtbmParseError("Truncated ROOT node")

        version = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        width = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        height = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        item_major = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        item_minor = struct.unpack_from("<I", data, offset)[0]
        offset += 4

        children, offset = self._parse_children(data, offset)

        node = {
            "type": OTBM_NODE_ROOT,
            "version": version,
            "width": width,
            "height": height,
            "item_major": item_major,
            "item_minor": item_minor,
            "children": children,
        }
        return node, offset

    def _parse_standard_node(
        self, data: bytes, offset: int, node_type: int
    ) -> Tuple[Dict[str, Any], int]:
        """
        Parse a standard node with 2-byte size field.

        Structure:
            [type: 1] [size: 2] [payload: size bytes]

        For MAP_DATA, the payload starts with metadata strings followed by children.
        For TILE/TILE_SQUARE/HOUSETILE, the payload has position data followed by ITEM children.
        For ITEM, the payload has item_id + optional attributes.
        For leaf nodes (MONSTER, TOWN, WAYPOINT), the payload is pure data.
        """
        if offset + 2 > len(data):
            raise OtbmParseError(
                f"Truncated node header at offset {offset} for type 0x{node_type:02X}"
            )

        size = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        end_offset = offset + size

        if end_offset > len(data):
            raise OtbmParseError(
                f"Node type 0x{node_type:02X} claims size {size} but only {len(data) - offset} bytes remain"
            )

        node_data = data[offset:end_offset]

        if node_type == OTBM_NODE_MAP_DATA:
            # MAP_DATA: payload = [desc_str] [spawn_str] [house_str] [children...]
            children, _ = self._parse_map_data_children(node_data)
            node = {
                "type": node_type,
                "size": size,
                "payload": node_data,
                "children": children,
            }
        elif node_type == OTBM_NODE_TILE_AREA:
            # TILE_AREA: payload = [base_x:2][base_y:2][base_z:1] + child nodes
            children, _ = self._parse_children(node_data, 5)
            node = {
                "type": node_type,
                "size": size,
                "payload": node_data,
                "children": children,
            }
        elif node_type == OTBM_NODE_SPAWN_AREA:
            # SPAWN_AREA: payload = [center_x:2][center_y:2][center_z:1][radius:1] + children
            children, _ = self._parse_children(node_data, 6)
            node = {
                "type": node_type,
                "size": size,
                "payload": node_data,
                "children": children,
            }
        elif node_type in self.CONTAINER_NODES:
            # Pure container: entire payload is child nodes
            children, _ = self._parse_children(node_data, 0)
            node = {
                "type": node_type,
                "size": size,
                "payload": node_data,
                "children": children,
            }
        elif node_type in self.TILE_NODES:
            # TILE nodes: payload = [offset_x:1][offset_y:1][opt attrs][ITEM children]
            # Children are NOT extracted here — NodeDecoder handles payload parsing
            node = {
                "type": node_type,
                "size": size,
                "payload": node_data,
                "children": [],
            }
        elif node_type == OTBM_NODE_ITEM:
            # ITEM nodes: payload = [item_id:2][opt attributes][children]
            # Children are NOT extracted here — NodeDecoder handles payload parsing
            node = {
                "type": node_type,
                "size": size,
                "payload": node_data,
                "children": [],
            }
        else:
            # Leaf node: pure payload, no children
            node = {
                "type": node_type,
                "size": size,
                "payload": node_data,
                "children": [],
            }

        return node, end_offset

    @staticmethod
    def _extract_item_children(data: bytes, min_offset: int) -> List[Dict[str, Any]]:
        """
        Extract ITEM child nodes from TILE or ITEM payload data.

        Scans for ITEM node markers (0x04) in the data starting from min_offset
        and parses any valid ITEM nodes found. Non-node attribute bytes between
        the header and the first ITEM child are skipped.

        Returns:
            List of child node dicts.
        """
        children: List[Dict[str, Any]] = []
        offset = min_offset
        while offset < len(data):
            # Look for ITEM node marker
            idx = data.find(bytes([OTBM_NODE_ITEM]), offset)
            if idx == -1:
                break
            # Try to parse an ITEM node at this position
            try:
                if idx + 3 > len(data):
                    break
                item_size = struct.unpack_from("<H", data, idx + 1)[0]
                if idx + 3 + item_size > len(data):
                    break
                child = {
                    "type": OTBM_NODE_ITEM,
                    "size": item_size,
                    "payload": data[idx + 3 : idx + 3 + item_size],
                    "children": [],
                }
                children.append(child)
                offset = idx + 3 + item_size
            except (struct.error, IndexError):
                offset = idx + 1
        return children

    def _parse_map_data_children(self, data: bytes) -> Tuple[List[Dict[str, Any]], int]:
        """
        Parse MAP_DATA payload which has mixed content:
            [desc_str][spawn_str][house_str][child_nodes...]

        Returns (children, offset_past_strings).
        """
        offset = 0
        # Parse description string (skip over it)
        if len(data) >= 2:
            desc_len = struct.unpack_from("<H", data, offset)[0]
            offset += 2 + desc_len
        # Parse spawn file string
        if len(data) > offset + 2:
            spawn_len = struct.unpack_from("<H", data, offset)[0]
            offset += 2 + spawn_len
        # Parse house file string
        if len(data) > offset + 2:
            house_len = struct.unpack_from("<H", data, offset)[0]
            offset += 2 + house_len
        # Remaining bytes are children
        children, _ = self._parse_children(data, offset)
        return children, offset

    def _parse_children_from_first_item(
        self, data: bytes, min_offset: int
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Parse children starting from the first ITEM node (type=0x04) found
        at or after min_offset. Any non-node data before the first ITEM
        is skipped.

        This handles TILE and ITEM payloads where attributes precede children.
        """
        # Find first ITEM node type marker
        item_marker = bytes([OTBM_NODE_ITEM])
        start = data.find(item_marker, min_offset)
        if start == -1:
            return [], len(data)
        return self._parse_children(data, start)

    def _parse_children(
        self, data: bytes, offset: int
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Parse child nodes from data starting at offset.

        Continues until data is exhausted or invalid.
        """
        children = []
        while offset < len(data):
            try:
                child, offset = self._parse_node(data, offset)
                children.append(child)
            except (struct.error, ValueError, IndexError, OtbmParseError):
                # If we can't parse more, stop
                break
        return children, offset

    # ------------------------------------------------------------------
    # Convenience methods for finding nodes
    # ------------------------------------------------------------------

    @staticmethod
    def find_children_of_type(
        node: Dict[str, Any], target_type: int
    ) -> List[Dict[str, Any]]:
        """Find all direct children of a node that match target_type."""
        return [c for c in node.get("children", []) if c.get("type") == target_type]

    @staticmethod
    def find_first_child_of_type(
        node: Dict[str, Any], target_type: int
    ) -> Optional[Dict[str, Any]]:
        """Find first direct child matching target_type."""
        for c in node.get("children", []):
            if c.get("type") == target_type:
                return c
        return None

    @staticmethod
    def find_all_descendants_of_type(
        node: Dict[str, Any], target_type: int
    ) -> List[Dict[str, Any]]:
        """Recursively find all descendants matching target_type."""
        results = []
        for child in node.get("children", []):
            if child.get("type") == target_type:
                results.append(child)
            results.extend(OtbmParser.find_all_descendants_of_type(child, target_type))
        return results

    # ------------------------------------------------------------------
    # Leaf node payload reading (delegates to NodeEncoder utilities)
    # ------------------------------------------------------------------

    @staticmethod
    def read_uint8(data: bytes, offset: int) -> Tuple[int, int]:
        return NodeEncoder.read_uint8(data, offset)

    @staticmethod
    def read_uint16(data: bytes, offset: int) -> Tuple[int, int]:
        return NodeEncoder.read_uint16(data, offset)

    @staticmethod
    def read_uint32(data: bytes, offset: int) -> Tuple[int, int]:
        return NodeEncoder.read_uint32(data, offset)

    @staticmethod
    def read_string(data: bytes, offset: int) -> Tuple[str, int]:
        return NodeEncoder.read_string(data, offset)

    @staticmethod
    def read_attributes(
        data: bytes, offset: int, end_offset: int
    ) -> Tuple[Dict[int, Any], int]:
        """
        Read attribute-value pairs from an item payload.

        OTBM item attributes use format:
            [attr_type: 1] [value: variable]

        Returns a dict mapping attribute type to value, and the new offset.
        """
        from .node_encoder import (
            ATTR_DESCRIPTION,
            ATTR_TILE_FLAGS,
            ATTR_ITEM,
            ATTR_COUNT,
            ATTR_ACTION_ID,
            ATTR_UNIQUE_ID,
            ATTR_TEXT,
            ATTR_DESC,
            ATTR_DURATION,
            ATTR_DECAYING_STATE,
            ATTR_WRITTEN_DATE,
            ATTR_WRITTEN_BY,
            ATTR_SLEEPERGUID,
            ATTR_SLEEPSTART,
            ATTR_CHARGES,
            ATTR_SUBTYPE,
            ATTR_EXT_FILE,
        )

        attrs: Dict[int, Any] = {}
        while offset < end_offset:
            attr_type = data[offset]
            offset += 1

            if attr_type == ATTR_DESCRIPTION:
                val, offset = NodeEncoder.read_string(data, offset)
                attrs[ATTR_DESCRIPTION] = val
            elif attr_type == ATTR_TILE_FLAGS:
                val, offset = NodeEncoder.read_uint32(data, offset)
                attrs[ATTR_TILE_FLAGS] = val
            elif attr_type == ATTR_ITEM:
                val, offset = NodeEncoder.read_uint16(data, offset)
                attrs[ATTR_ITEM] = val
            elif attr_type == ATTR_COUNT:
                val, offset = NodeEncoder.read_uint8(data, offset)
                attrs[ATTR_COUNT] = val
            elif attr_type == ATTR_ACTION_ID:
                val, offset = NodeEncoder.read_uint16(data, offset)
                attrs[ATTR_ACTION_ID] = val
            elif attr_type == ATTR_UNIQUE_ID:
                val, offset = NodeEncoder.read_uint16(data, offset)
                attrs[ATTR_UNIQUE_ID] = val
            elif attr_type == ATTR_TEXT:
                val, offset = NodeEncoder.read_string(data, offset)
                attrs[ATTR_TEXT] = val
            elif attr_type == ATTR_DESC:
                val, offset = NodeEncoder.read_string(data, offset)
                attrs[ATTR_DESC] = val
            elif attr_type == ATTR_DURATION:
                val, offset = NodeEncoder.read_uint32(data, offset)
                attrs[ATTR_DURATION] = val
            elif attr_type == ATTR_DECAYING_STATE:
                val, offset = NodeEncoder.read_uint8(data, offset)
                attrs[ATTR_DECAYING_STATE] = val
            elif attr_type == ATTR_WRITTEN_DATE:
                val, offset = NodeEncoder.read_uint32(data, offset)
                attrs[ATTR_WRITTEN_DATE] = val
            elif attr_type == ATTR_WRITTEN_BY:
                val, offset = NodeEncoder.read_string(data, offset)
                attrs[ATTR_WRITTEN_BY] = val
            elif attr_type == ATTR_SLEEPERGUID:
                val, offset = NodeEncoder.read_uint32(data, offset)
                attrs[ATTR_SLEEPERGUID] = val
            elif attr_type == ATTR_SLEEPSTART:
                val, offset = NodeEncoder.read_uint32(data, offset)
                attrs[ATTR_SLEEPSTART] = val
            elif attr_type == ATTR_CHARGES:
                val, offset = NodeEncoder.read_uint8(data, offset)
                attrs[ATTR_CHARGES] = val
            elif attr_type == ATTR_SUBTYPE:
                val, offset = NodeEncoder.read_uint8(data, offset)
                attrs[ATTR_SUBTYPE] = val
            elif attr_type == ATTR_EXT_FILE:
                val, offset = NodeEncoder.read_string(data, offset)
                attrs[ATTR_EXT_FILE] = val
            else:
                # Unknown attribute — break
                break

        return attrs, offset
