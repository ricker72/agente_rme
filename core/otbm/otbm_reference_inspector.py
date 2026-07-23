from __future__ import annotations

import json
import struct
from collections import Counter
from pathlib import Path
from typing import Any

from .compatibility.otbm_constants import OTBM_ACCEPTED_IDENTIFIERS

NODE_START = 0xFE
NODE_END = 0xFF
ESCAPE_BYTE = 0xFD

NODE_NAMES = {
    0x00: "ROOT",
    0x02: "MAP_DATA",
    0x04: "TILE_AREA",
    0x05: "TILE",
    0x06: "ITEM",
    0x09: "SPAWNS",
    0x0A: "SPAWN_AREA",
    0x0B: "MONSTER",
    0x0C: "TOWNS",
    0x0D: "TOWN",
    0x0F: "WAYPOINTS",
    0x10: "WAYPOINT",
}

CUSTOM_NODE_TYPES = {
    0x11: "REGION",
    0x12: "CITY",
    0x13: "STRUCTURE",
}


def inspect_otbm_file(path: str | Path, max_nodes: int = 5000) -> dict[str, Any]:
    file_path = Path(path)
    data = file_path.read_bytes()
    inspector = _Inspector(data, max_nodes=max_nodes)
    return inspector.inspect(str(file_path))


def write_json(path: str | Path, payload: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


class _Inspector:
    def __init__(self, data: bytes, max_nodes: int) -> None:
        self.data = data
        self.max_nodes = max_nodes
        self.truncated = False
        self.tile_areas: list[dict[str, Any]] = []
        self.tiles: list[dict[str, Any]] = []
        self.items: list[dict[str, Any]] = []
        self.towns: list[dict[str, Any]] = []
        self.waypoints: list[dict[str, Any]] = []
        self.attributes: list[int] = []
        self.node_counter: Counter[int] = Counter()
        self.node_tree: list[dict[str, Any]] = []
        self.unbalanced_end_markers = 0
        self.escaping = {
            "escape_markers": data.count(bytes([ESCAPE_BYTE])),
            "escaped_node_starts": data.count(bytes([ESCAPE_BYTE, NODE_START])),
            "escaped_node_ends": data.count(bytes([ESCAPE_BYTE, NODE_END])),
            "escaped_escape_bytes": data.count(bytes([ESCAPE_BYTE, ESCAPE_BYTE])),
        }

    def inspect(self, label: str) -> dict[str, Any]:
        root_marker = self.data[4] if len(self.data) > 4 else None
        root_type = self.data[5] if len(self.data) > 5 else None
        root_payload_size = max(0, len(self.data) - 6)
        root_header = self._read_root_header(6) if root_marker == NODE_START else {}

        if self.data[:4] in OTBM_ACCEPTED_IDENTIFIERS and root_marker == NODE_START:
            try:
                node, offset = self._parse_node(4, None, None, 0)
                self.node_tree.append(node)
                if offset < len(self.data):
                    self.unbalanced_end_markers += self.data[offset:].count(NODE_END)
            except ValueError as exc:
                self.node_tree.append({"error": str(exc)})

        return {
            "file": label,
            "file_size": len(self.data),
            "root_marker": root_marker,
            "root_type": root_type,
            "root_payload_size": root_payload_size,
            "header_fields": root_header,
            "node_counts": {NODE_NAMES.get(k, hex(k)): v for k, v in sorted(self.node_counter.items())},
            "node_tree": self.node_tree,
            "tile_areas": self.tile_areas,
            "tile_coordinates": [
                {"x": t["x"], "y": t["y"], "z": t["z"]} for t in self.tiles
            ],
            "tiles": self.tiles,
            "item_ids": [item["id"] for item in self.items],
            "items": self.items,
            "towns": self.towns,
            "waypoints": self.waypoints,
            "attribute_ids": sorted(set(self.attributes)),
            "delimiter_balance": {
                "node_starts": self.data.count(bytes([NODE_START])),
                "node_ends": self.data.count(bytes([NODE_END])),
                "balanced": self.unbalanced_end_markers == 0,
                "unbalanced_end_markers": self.unbalanced_end_markers,
            },
            "escaping_statistics": self.escaping,
            "custom_nodes_present": [
                CUSTOM_NODE_TYPES[node_type]
                for node_type in sorted(self.node_counter)
                if node_type in CUSTOM_NODE_TYPES
            ],
            "parse_truncated": self.truncated,
            "parse_node_limit": self.max_nodes,
        }

    def _parse_node(
        self,
        offset: int,
        current_area: dict[str, int] | None,
        current_tile: dict[str, Any] | None,
        depth: int,
    ) -> tuple[dict[str, Any], int]:
        if offset + 2 > len(self.data) or self.data[offset] != NODE_START:
            raise ValueError(f"expected node start at offset {offset}")
        if sum(self.node_counter.values()) >= self.max_nodes:
            self.truncated = True
            return {
                "type": None,
                "name": "TRUNCATED",
                "offset": offset,
                "depth": depth,
                "children": [],
            }, len(self.data)

        start = offset
        node_type = self.data[offset + 1]
        self.node_counter[node_type] += 1
        offset += 2

        attrs, offset = self._read_attrs(node_type, offset)
        summary: dict[str, Any] = {
            "type": node_type,
            "name": NODE_NAMES.get(node_type, f"UNKNOWN_{node_type:02X}"),
            "offset": start,
            "depth": depth,
            "attrs_hex": attrs.hex(),
            "children": [],
        }

        area = current_area
        tile = current_tile
        if node_type == 0x00:
            summary["header"] = self._decode_root_header(attrs)
        elif node_type == 0x02:
            summary["map_attributes"] = self._decode_map_attrs(attrs)
        elif node_type == 0x04 and len(attrs) >= 5:
            area = {
                "base_x": struct.unpack_from("<H", attrs, 0)[0],
                "base_y": struct.unpack_from("<H", attrs, 2)[0],
                "base_z": attrs[4],
                "offset": start,
            }
            self.tile_areas.append(dict(area))
            summary.update(area)
        elif node_type in (0x05, 0x0E) and area is not None and len(attrs) >= 2:
            attribute_offset = 6 if node_type == 0x0E else 2
            tile = {
                "x": area["base_x"] + attrs[0],
                "y": area["base_y"] + attrs[1],
                "z": area["base_z"],
                "offset_x": attrs[0],
                "offset_y": attrs[1],
                "items": [],
                "offset": start,
            }
            if node_type == 0x0E and len(attrs) >= 6:
                tile["house_id"] = struct.unpack_from("<I", attrs, 2)[0]
            self.tiles.append(tile)
            summary.update({k: tile[k] for k in ("x", "y", "z", "offset_x", "offset_y")})
            if "house_id" in tile:
                summary["house_id"] = tile["house_id"]
            if len(attrs) > attribute_offset:
                self.attributes.extend(
                    attrs[attribute_offset::5]
                    if attrs[attribute_offset] == 0x03
                    else attrs[attribute_offset:]
                )
        elif node_type == 0x06 and len(attrs) >= 2:
            item = {"id": struct.unpack_from("<H", attrs, 0)[0], "offset": start}
            self.items.append(item)
            if tile is not None:
                tile["items"].append(item["id"])
            summary.update(item)
            self.attributes.extend(self._item_attr_ids(attrs[2:]))
        elif node_type == 0x0D and len(attrs) >= 11:
            town_id = struct.unpack_from("<I", attrs, 0)[0]
            name, pos = self._read_string_from_attrs(attrs, 4)
            if pos + 5 <= len(attrs):
                town = {
                    "town_id": town_id,
                    "name": name,
                    "temple_x": struct.unpack_from("<H", attrs, pos)[0],
                    "temple_y": struct.unpack_from("<H", attrs, pos + 2)[0],
                    "temple_z": attrs[pos + 4],
                    "offset": start,
                }
                self.towns.append(town)
                summary.update(town)
        elif node_type == 0x10 and len(attrs) >= 7:
            name, pos = self._read_string_from_attrs(attrs, 0)
            if pos + 5 <= len(attrs):
                waypoint = {
                    "name": name,
                    "x": struct.unpack_from("<H", attrs, pos)[0],
                    "y": struct.unpack_from("<H", attrs, pos + 2)[0],
                    "z": attrs[pos + 4],
                    "offset": start,
                }
                self.waypoints.append(waypoint)
                summary.update(waypoint)

        while offset < len(self.data):
            byte = self.data[offset]
            if byte == NODE_END:
                summary["end_offset"] = offset
                return summary, offset + 1
            if byte == NODE_START:
                child, offset = self._parse_node(offset, area, tile, depth + 1)
                summary["children"].append(child)
                continue
            offset += 1

        self.unbalanced_end_markers += 1
        summary["missing_end"] = True
        return summary, offset

    def _read_attrs(self, node_type: int, offset: int) -> tuple[bytes, int]:
        length = self._fixed_attr_length(node_type)
        if length is not None:
            return self._read_escaped_exact(offset, length)

        attrs = bytearray()
        while offset < len(self.data):
            byte = self.data[offset]
            if byte in (NODE_START, NODE_END):
                break
            if byte == ESCAPE_BYTE and offset + 1 < len(self.data):
                attrs.append(self.data[offset + 1])
                offset += 2
            else:
                attrs.append(byte)
                offset += 1
        return bytes(attrs), offset

    def _read_escaped_exact(self, offset: int, length: int) -> tuple[bytes, int]:
        attrs = bytearray()
        while offset < len(self.data) and len(attrs) < length:
            byte = self.data[offset]
            if byte == ESCAPE_BYTE and offset + 1 < len(self.data):
                attrs.append(self.data[offset + 1])
                offset += 2
            else:
                attrs.append(byte)
                offset += 1
        return bytes(attrs), offset

    @staticmethod
    def _fixed_attr_length(node_type: int) -> int | None:
        return {
            0x00: 16,
            0x04: 5,
        }.get(node_type)

    def _read_root_header(self, offset: int) -> dict[str, Any]:
        if offset + 16 > len(self.data):
            return {}
        return self._decode_root_header(self.data[offset:offset + 16])

    @staticmethod
    def _decode_root_header(attrs: bytes) -> dict[str, Any]:
        if len(attrs) < 16:
            return {}
        return {
            "version": struct.unpack_from("<I", attrs, 0)[0],
            "width": struct.unpack_from("<H", attrs, 4)[0],
            "height": struct.unpack_from("<H", attrs, 6)[0],
            "item_major_version": struct.unpack_from("<I", attrs, 8)[0],
            "item_minor_version": struct.unpack_from("<I", attrs, 12)[0],
        }

    @staticmethod
    def _decode_map_attrs(attrs: bytes) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        offset = 0
        while offset + 3 <= len(attrs):
            attr_id = attrs[offset]
            size = struct.unpack_from("<H", attrs, offset + 1)[0]
            offset += 3
            if offset + size > len(attrs):
                break
            value = attrs[offset:offset + size]
            out.append({
                "id": attr_id,
                "value": value.decode("utf-8", errors="replace"),
            })
            offset += size
        return out

    @staticmethod
    def _read_string_from_attrs(attrs: bytes, offset: int) -> tuple[str, int]:
        if offset + 2 > len(attrs):
            return "", offset
        size = struct.unpack_from("<H", attrs, offset)[0]
        offset += 2
        if offset + size > len(attrs):
            size = len(attrs) - offset
        return attrs[offset:offset + size].decode("utf-8", errors="replace"), offset + size

    @staticmethod
    def _item_attr_ids(attrs: bytes) -> list[int]:
        ids: list[int] = []
        offset = 0
        while offset < len(attrs):
            attr_id = attrs[offset]
            ids.append(attr_id)
            offset += 1
            if attr_id in (0x0F, 0x13, 0x16, 0x11):
                offset += 1
            elif attr_id in (0x04, 0x05):
                offset += 2
            elif attr_id in (0x10,):
                offset += 4
            elif attr_id in (0x06, 0x07):
                if offset + 2 > len(attrs):
                    break
                size = struct.unpack_from("<H", attrs, offset)[0]
                offset += 2 + size
            else:
                break
        return ids
