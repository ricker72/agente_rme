"""
Node Decoder — decodes individual OTBM node types into structured Python dicts.

Takes raw parsed nodes from OtbmParser and decodes each type:
    - ROOT → map header info
    - MAP_DATA → description, spawn file, house file
    - TILE_AREA → base coords + child tiles
    - TILE → tile position, flags, ground + items
    - ITEM → item_id + attributes
    - SPAWNS → container
    - SPAWN_AREA → center, radius + monster children
    - MONSTER → name, direction, spawntime
    - TOWNS → container
    - TOWN → town_id, name, temple pos
    - WAYPOINTS → container
    - WAYPOINT → name, position
    - HOUSETILE → position, house_id + items
"""

from __future__ import annotations

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
    OTBM_NODE_MONSTER,
    OTBM_NODE_TOWNS,
    OTBM_NODE_TOWN,
    OTBM_NODE_HOUSETILE,
    OTBM_NODE_WAYPOINTS,
    OTBM_NODE_WAYPOINT,
    ATTR_DESCRIPTION,
    ATTR_TILE_FLAGS,
    ATTR_ITEM,
    ATTR_COUNT,
    ATTR_ACTION_ID,
    ATTR_UNIQUE_ID,
    ATTR_TEXT,
    ATTR_DESC,
    ATTR_EXT_HOUSE_FILE,
    ATTR_EXT_SPAWN_FILE,
    ATTR_DURATION,
    ATTR_DECAYING_STATE,
    ATTR_WRITTEN_DATE,
    ATTR_WRITTEN_BY,
    ATTR_SLEEPERGUID,
    ATTR_SLEEPSTART,
    ATTR_CHARGES,
    ATTR_SUBTYPE,
    TILESTATE_NONE,
    TILESTATE_PROTECTIONZONE,
    TILESTATE_NOPVPZONE,
    TILESTATE_NOLOGOUT,
    TILESTATE_PVPZONE,
)


class NodeDecodeError(Exception):
    """Raised when a node cannot be decoded."""
    pass


class NodeDecoder:
    """
    Decodes parsed OTBM nodes into structured Python dicts.

    Each decode_* method takes a parsed node dict (from OtbmParser)
    and returns a decoded dict with meaningful keys.
    """

    def __init__(self):
        self._encoder = NodeEncoder()

    # ------------------------------------------------------------------
    # Public decode methods
    # ------------------------------------------------------------------

    def decode_root(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode ROOT node.

        Returns:
            {
                "version": int,
                "width": int,
                "height": int,
                "item_major": int,
                "item_minor": int,
                "map_data": dict or None,
                "tile_areas": [dict, ...],
                "spawns": dict or None,
                "towns": dict or None,
                "waypoints": dict or None,
            }
        """
        result = {
            "version": node.get("version", 0),
            "width": node.get("width", 0),
            "height": node.get("height", 0),
            "item_major": node.get("item_major", 3),
            "item_minor": node.get("item_minor", 57),
            "map_data": None,
            "tile_areas": [],
            "spawns": None,
            "towns": None,
            "waypoints": None,
        }

        map_data_node = self._find_first(node, OTBM_NODE_MAP_DATA)
        if map_data_node:
            decoded_map = self.decode_map_data(map_data_node)
            result["map_data"] = decoded_map

            # Extract children from map_data
            for child in map_data_node.get("children", []):
                child_type = child.get("type")
                if child_type == OTBM_NODE_TILE_AREA:
                    result["tile_areas"].append(child)
                elif child_type == OTBM_NODE_SPAWNS:
                    result["spawns"] = child
                elif child_type == OTBM_NODE_TOWNS:
                    result["towns"] = child
                elif child_type == OTBM_NODE_WAYPOINTS:
                    result["waypoints"] = child

        return result

    def decode_map_data(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode MAP_DATA node.

        MAP_DATA payload:
            [description: string] [spawn_file: string] [house_file: string]

        Returns:
            {
                "description": str,
                "spawn_file": str,
                "house_file": str,
            }
        """
        payload = node.get("payload", b"")
        offset = 0
        description = ""
        spawn_file = ""
        house_file = ""

        if len(payload) > 0:
            description, offset = NodeEncoder.read_string(payload, offset)
        if len(payload) > offset:
            spawn_file, offset = NodeEncoder.read_string(payload, offset)
        if len(payload) > offset:
            house_file, _ = NodeEncoder.read_string(payload, offset)

        return {
            "description": description,
            "spawn_file": spawn_file,
            "house_file": house_file,
        }

    def decode_tile_area(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode TILE_AREA node.

        TILE_AREA payload:
            [base_x: uint16] [base_y: uint16] [base_z: uint8]

        Returns:
            {
                "base_x": int,
                "base_y": int,
                "base_z": int,
                "tiles": [dict, ...],  # decoded tile children
            }
        """
        payload = node.get("payload", b"")
        if len(payload) < 5:
            raise NodeDecodeError("TILE_AREA payload too short")

        base_x, offset = NodeEncoder.read_uint16(payload, 0)
        base_y, offset = NodeEncoder.read_uint16(payload, offset)
        base_z, offset = NodeEncoder.read_uint8(payload, offset)

        tiles = []
        for child in node.get("children", []):
            child_type = child.get("type")
            if child_type == OTBM_NODE_TILE:
                decoded = self.decode_tile(child, base_x, base_y, base_z)
                tiles.append(decoded)
            elif child_type == OTBM_NODE_HOUSETILE:
                decoded = self.decode_house_tile(child, base_x, base_y, base_z)
                tiles.append(decoded)

        return {
            "base_x": base_x,
            "base_y": base_y,
            "base_z": base_z,
            "tiles": tiles,
        }

    def decode_tile(
        self, node: Dict[str, Any],
        area_base_x: int = 0,
        area_base_y: int = 0,
        area_base_z: int = 0,
    ) -> Dict[str, Any]:
        """
        Decode TILE node.

        TILE payload:
            [offset_x: uint8] [offset_y: uint8]
            Optional attributes: ATTR_TILE_FLAGS (uint32)
            [children ITEM nodes embedded in payload]

        Returns:
            {
                "x": int,
                "y": int,
                "z": int,
                "flags": int,
                "items": [dict, ...],
                "ground": dict or None,
            }
        """
        payload = node.get("payload", b"")
        if len(payload) < 2:
            raise NodeDecodeError("TILE payload too short")

        offset_x, offset = NodeEncoder.read_uint8(payload, 0)
        offset_y, offset = NodeEncoder.read_uint8(payload, offset)

        x = area_base_x + offset_x
        y = area_base_y + offset_y
        z = area_base_z

        # Decode ITEM children directly from payload bytes.
        # This method handles both ATTR_TILE_FLAGS (0x04+uint32) and ITEM (0x04+size+payload)
        # because both start with 0x04 byte marker.
        items, flags = self._decode_items_from_payload(payload, offset)

        # First item is typically the ground
        ground = items[0] if items else None
        # Remaining items are additional items
        additional_items = items[1:] if len(items) > 1 else []

        return {
            "x": x,
            "y": y,
            "z": z,
            "flags": flags,
            "ground": ground,
            "items": additional_items,
            "all_items": items,
        }

    def decode_house_tile(
        self, node: Dict[str, Any],
        area_base_x: int = 0,
        area_base_y: int = 0,
        area_base_z: int = 0,
    ) -> Dict[str, Any]:
        """
        Decode HOUSETILE node.

        HOUSETILE payload:
            [offset_x: uint8] [offset_y: uint8] [house_id: uint32]
        Children: ITEM nodes

        Returns:
            {
                "x": int,
                "y": int,
                "z": int,
                "house_id": int,
                "items": [dict, ...],
                "ground": dict or None,
                "is_house": True,
            }
        """
        payload = node.get("payload", b"")
        if len(payload) < 6:
            raise NodeDecodeError("HOUSETILE payload too short")

        offset_x, offset = NodeEncoder.read_uint8(payload, 0)
        offset_y, offset = NodeEncoder.read_uint8(payload, offset)
        house_id, _ = NodeEncoder.read_uint32(payload, offset)

        x = area_base_x + offset_x
        y = area_base_y + offset_y
        z = area_base_z

        items = []
        for child in node.get("children", []):
            if child.get("type") == OTBM_NODE_ITEM:
                decoded_item = self.decode_item(child)
                items.append(decoded_item)

        ground = items[0] if items else None

        return {
            "x": x,
            "y": y,
            "z": z,
            "house_id": house_id,
            "flags": TILESTATE_PROTECTIONZONE,
            "ground": ground,
            "items": items[1:] if len(items) > 1 else [],
            "all_items": items,
            "is_house": True,
        }

    def decode_item(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode ITEM node.

        ITEM payload:
            [item_id: uint16]
            Optional attributes (attr_type + value pairs)

        Returns:
            {
                "item_id": int,
                "attributes": {attr_type: value, ...},
                "children": [dict, ...],  # for container items
            }
        """
        payload = node.get("payload", b"")
        if len(payload) < 2:
            raise NodeDecodeError("ITEM payload too short (< 2 bytes)")

        item_id, offset = NodeEncoder.read_uint16(payload, 0)

        # Read attributes from remaining payload
        attributes = {}
        if len(payload) > offset:
            attrs, _ = self._read_attributes(payload, offset, len(payload))
            attributes = attrs

        # Decode child items (for containers)
        children = []
        for child in node.get("children", []):
            if child.get("type") == OTBM_NODE_ITEM:
                decoded = self.decode_item(child)
                children.append(decoded)

        return {
            "item_id": item_id,
            "attributes": attributes,
            "children": children,
        }

    def decode_spawns(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode SPAWNS container node.

        Returns:
            {
                "spawn_areas": [dict, ...],
            }
        """
        spawn_areas = []
        for child in node.get("children", []):
            if child.get("type") == OTBM_NODE_SPAWN_AREA:
                decoded = self.decode_spawn_area(child)
                spawn_areas.append(decoded)

        return {"spawn_areas": spawn_areas}

    def decode_spawn_area(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode SPAWN_AREA node.

        SPAWN_AREA payload:
            [center_x: uint16] [center_y: uint16] [center_z: uint8] [radius: uint8]

        Returns:
            {
                "center_x": int,
                "center_y": int,
                "center_z": int,
                "radius": int,
                "monsters": [dict, ...],
            }
        """
        payload = node.get("payload", b"")
        if len(payload) < 6:
            raise NodeDecodeError("SPAWN_AREA payload too short")

        center_x, offset = NodeEncoder.read_uint16(payload, 0)
        center_y, offset = NodeEncoder.read_uint16(payload, offset)
        center_z, offset = NodeEncoder.read_uint8(payload, offset)
        radius, _ = NodeEncoder.read_uint8(payload, offset)

        monsters = []
        for child in node.get("children", []):
            if child.get("type") == OTBM_NODE_MONSTER:
                decoded = self.decode_monster(child)
                monsters.append(decoded)

        return {
            "center_x": center_x,
            "center_y": center_y,
            "center_z": center_z,
            "radius": radius,
            "monsters": monsters,
        }

    def decode_monster(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode MONSTER node.

        MONSTER payload:
            [name: string] [direction: uint8] [spawntime: uint32]

        Returns:
            {
                "name": str,
                "direction": int,
                "spawntime": int,
            }
        """
        payload = node.get("payload", b"")
        if len(payload) < 6:
            raise NodeDecodeError("MONSTER payload too short")

        name, offset = NodeEncoder.read_string(payload, 0)
        direction = payload[offset]
        offset += 1
        spawntime, _ = NodeEncoder.read_uint32(payload, offset)

        return {
            "name": name,
            "direction": direction,
            "spawntime": spawntime,
        }

    def decode_towns(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode TOWNS container node.

        Returns:
            {
                "towns": [dict, ...],
            }
        """
        towns = []
        for child in node.get("children", []):
            if child.get("type") == OTBM_NODE_TOWN:
                decoded = self.decode_town(child)
                towns.append(decoded)

        return {"towns": towns}

    def decode_town(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode TOWN node.

        TOWN payload:
            [town_id: uint32] [name: string] [temple_x: uint16]
            [temple_y: uint16] [temple_z: uint8]

        Returns:
            {
                "town_id": int,
                "name": str,
                "temple_x": int,
                "temple_y": int,
                "temple_z": int,
            }
        """
        payload = node.get("payload", b"")
        if len(payload) < 9:
            raise NodeDecodeError("TOWN payload too short")

        town_id, offset = NodeEncoder.read_uint32(payload, 0)
        name, offset = NodeEncoder.read_string(payload, offset)
        temple_x, offset = NodeEncoder.read_uint16(payload, offset)
        temple_y, offset = NodeEncoder.read_uint16(payload, offset)
        temple_z, _ = NodeEncoder.read_uint8(payload, offset)

        return {
            "town_id": town_id,
            "name": name,
            "temple_x": temple_x,
            "temple_y": temple_y,
            "temple_z": temple_z,
        }

    def decode_waypoints(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode WAYPOINTS container node.

        Returns:
            {
                "waypoints": [dict, ...],
            }
        """
        waypoints = []
        for child in node.get("children", []):
            if child.get("type") == OTBM_NODE_WAYPOINT:
                decoded = self.decode_waypoint(child)
                waypoints.append(decoded)

        return {"waypoints": waypoints}

    def decode_waypoint(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode WAYPOINT node.

        WAYPOINT payload:
            [name: string] [x: uint16] [y: uint16] [z: uint8]

        Returns:
            {
                "name": str,
                "x": int,
                "y": int,
                "z": int,
            }
        """
        payload = node.get("payload", b"")
        if len(payload) < 6:
            raise NodeDecodeError("WAYPOINT payload too short")

        name, offset = NodeEncoder.read_string(payload, 0)
        x, offset = NodeEncoder.read_uint16(payload, offset)
        y, offset = NodeEncoder.read_uint16(payload, offset)
        z, _ = NodeEncoder.read_uint8(payload, offset)

        return {
            "name": name,
            "x": x,
            "y": y,
            "z": z,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _decode_items_from_payload(payload: bytes, offset: int) -> Tuple[List[Dict[str, Any]], int]:
        """
        Extract ITEM nodes from TILE payload bytes, handling ATTR_TILE_FLAGS ambiguity.

        TILE payload after position bytes:
            [opt ATTR_TILE_FLAGS: 0x04 + uint32(5 bytes)] [ITEM nodes...]

        ATTR_TILE_FLAGS is detected when:
          - Byte at offset is 0x04
          - Consuming 5 bytes (0x04 + uint32) leaves another 0x04 byte (next ITEM)
            OR the uint32 value looks like a known tile flag (<= 0x003F)

        Returns:
            (items: list of item dicts, flags: int)
        """
        import struct as _struct

        items: List[Dict[str, Any]] = []
        flags = TILESTATE_NONE

        # Check for ATTR_TILE_FLAGS before the first item
        if offset + 5 <= len(payload) and payload[offset] == 0x04:
            potential_flags = _struct.unpack_from("<I", payload, offset + 1)[0]
            peek = offset + 5
            has_next_item = peek < len(payload) and payload[peek] == 0x04
            is_plausible_flags = potential_flags <= 0x003F

            if has_next_item or is_plausible_flags:
                flags = potential_flags
                offset += 5

        # Parse ITEM nodes: [type:1][size:2][payload:size]
        while offset < len(payload):
            if payload[offset] != OTBM_NODE_ITEM:
                break
            if offset + 3 > len(payload):
                break
            item_size = _struct.unpack_from("<H", payload, offset + 1)[0]
            if item_size < 2 or offset + 3 + item_size > len(payload):
                break
            item_payload = payload[offset + 3:offset + 3 + item_size]
            item_id = _struct.unpack_from("<H", item_payload, 0)[0]
            attrs: Dict[int, Any] = {}
            if len(item_payload) > 2:
                attrs, _ = NodeDecoder._read_attributes(item_payload, 2, len(item_payload))
            items.append({
                "item_id": item_id,
                "attributes": attrs,
                "children": [],
            })
            offset = offset + 3 + item_size

        return items, flags

    @staticmethod
    def _find_first(node: Dict[str, Any], target_type: int) -> Optional[Dict[str, Any]]:
        """Find first child of given type."""
        for child in node.get("children", []):
            if child.get("type") == target_type:
                return child
        return None

    @staticmethod
    def _read_attributes(
        data: bytes, offset: int, end_offset: int
    ) -> Tuple[Dict[int, Any], int]:
        """Read attribute-value pairs from item payload."""
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
                val = data[offset]
                offset += 1
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
                val = data[offset]
                offset += 1
                attrs[ATTR_CHARGES] = val
            elif attr_type == ATTR_SUBTYPE:
                val = data[offset]
                offset += 1
                attrs[ATTR_SUBTYPE] = val
            elif attr_type == ATTR_EXT_FILE:
                val, offset = NodeEncoder.read_string(data, offset)
                attrs[ATTR_EXT_FILE] = val
            else:
                # Unknown attribute — skip 1 byte value
                offset += 1
                continue

        return attrs, offset

    def decode_all_tiles(self, root_node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convenience method: extract all tiles from the entire OTBM tree.

        Returns a flat list of decoded tiles.
        """
        decoded_root = self.decode_root(root_node)
        all_tiles = []

        for area_node in decoded_root.get("tile_areas", []):
            area_decoded = self.decode_tile_area(area_node)
            all_tiles.extend(area_decoded.get("tiles", []))

        return all_tiles

    def decode_all_spawns(self, root_node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convenience method: extract all spawn entries from the entire OTBM tree.

        Returns a flat list of spawn dicts with monster info.
        """
        decoded_root = self.decode_root(root_node)
        spawns_node = decoded_root.get("spawns")

        if not spawns_node:
            return []

        spawns_decoded = self.decode_spawns(spawns_node)
        result = []

        for area in spawns_decoded.get("spawn_areas", []):
            for monster in area.get("monsters", []):
                result.append({
                    "x": area["center_x"],
                    "y": area["center_y"],
                    "z": area["center_z"],
                    "radius": area["radius"],
                    "name": monster["name"],
                    "direction": monster["direction"],
                    "spawntime": monster["spawntime"],
                })

        return result

    def decode_all_towns(self, root_node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all towns from the OTBM tree."""
        decoded_root = self.decode_root(root_node)
        towns_node = decoded_root.get("towns")
        if not towns_node:
            return []
        towns_decoded = self.decode_towns(towns_node)
        return towns_decoded.get("towns", [])

    def decode_all_waypoints(self, root_node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all waypoints from the OTBM tree."""
        decoded_root = self.decode_root(root_node)
        wp_node = decoded_root.get("waypoints")
        if not wp_node:
            return []
        wp_decoded = self.decode_waypoints(wp_node)
        return wp_decoded.get("waypoints", [])