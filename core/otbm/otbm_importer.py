"""
OTBM Importer — reads .otbm files and converts them to WorldModel.

Entry point for importing OTBM maps into the RME Agent system.

Pipeline:
    .otbm file
    -> canonical 00000000 identifier validation
    -> FE/FF/FD delimiter traversal
    -> bounded tile-area index and lazy chunk extraction

Usage:
    importer = OTBMImporter()
    result = importer.import_file("map.otbm")
    world_model = result["world_model"]

Statistics:
    report = importer.import_file("map.otbm")
    print(report["stats"]["tiles"])  # number of tiles imported
"""

from __future__ import annotations

import mmap
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .compatibility.otbm_constants import OTBM_ACCEPTED_IDENTIFIERS
from .otbm_validator import OtbmValidator


class OtbmParseError(ValueError):
    """Raised when a canonical Canary/RME OTBM stream is malformed."""


RME_NODE_START = 0xFE
RME_NODE_END = 0xFF
RME_ESCAPE = 0xFD


RME_NODE_NAMES = {
    0x00: "ROOT",
    0x01: "ROOTV1",
    0x02: "MAP_DATA",
    0x04: "TILE_AREA",
    0x05: "TILE",
    0x06: "ITEM",
    0x09: "SPAWNS",
    0x0A: "SPAWN_AREA",
    0x0B: "MONSTER",
    0x0C: "TOWNS",
    0x0D: "TOWN",
    0x0E: "HOUSETILE",
    0x0F: "WAYPOINTS",
    0x10: "WAYPOINT",
    0x11: "SPAWN_NPC_AREA",
    0x12: "SPAWNS_NPC",
    0x13: "TILE_ZONE",
}


@dataclass(frozen=True)
class OTBMNode:
    node_type: int
    offset: int
    payload: bytes
    attrs: bytes
    depth: int
    delimiter: int | None
    delimiter_offset: int
    next_offset: int

    @property
    def name(self) -> str:
        return RME_NODE_NAMES.get(self.node_type, f"UNKNOWN_{self.node_type:02X}")


@dataclass
class OTBMTileAreaIndex:
    base_x: int
    base_y: int
    z: int
    offset: int
    estimated_tile_count: int = 0

    @property
    def max_x(self) -> int:
        return self.base_x + 255

    @property
    def max_y(self) -> int:
        return self.base_y + 255


@dataclass
class OTBMTraversalStats:
    nodes_visited: int = 0
    node_counts: Dict[str, int] = field(default_factory=dict)
    tile_areas_detected: int = 0
    estimated_tiles: int = 0
    floors_detected: set[int] = field(default_factory=set)
    truncated: bool = False
    diagnostics: list[str] = field(default_factory=list)


@dataclass
class OTBMSectionIndex:
    metadata: Dict[str, Any]
    map_attributes: Dict[str, str]
    tile_areas: list[OTBMTileAreaIndex]
    stats: OTBMTraversalStats
    file_size: int
    elapsed_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata,
            "map_attributes": self.map_attributes,
            "tile_areas": [area.__dict__ for area in self.tile_areas],
            "stats": {
                "nodes_visited": self.stats.nodes_visited,
                "node_counts": self.stats.node_counts,
                "tile_areas_detected": self.stats.tile_areas_detected,
                "estimated_tiles": self.stats.estimated_tiles,
                "floors_detected": sorted(self.stats.floors_detected),
                "truncated": self.stats.truncated,
                "diagnostics": self.stats.diagnostics,
            },
            "file_size": self.file_size,
            "elapsed_seconds": self.elapsed_seconds,
        }


class OTBMAttributeReader:
    @staticmethod
    def u16(data: bytes, offset: int) -> int:
        return int.from_bytes(data[offset : offset + 2], "little")

    @staticmethod
    def u32(data: bytes, offset: int) -> int:
        return int.from_bytes(data[offset : offset + 4], "little")

    @staticmethod
    def string(data: bytes, offset: int) -> tuple[str, int]:
        if offset + 2 > len(data):
            return "", len(data)
        size = OTBMAttributeReader.u16(data, offset)
        offset += 2
        end = min(len(data), offset + size)
        return data[offset:end].decode("utf-8", errors="replace"), end

    @staticmethod
    def parse_root(attrs: bytes) -> Dict[str, Any]:
        if len(attrs) < 16:
            raise ValueError("root attrs too small")
        return {
            "root_payload_type": attrs[0],
            "version": OTBMAttributeReader.u32(attrs, 1),
            "width": OTBMAttributeReader.u16(attrs, 5),
            "height": OTBMAttributeReader.u16(attrs, 7),
            "item_major_version": OTBMAttributeReader.u32(attrs, 9),
            "item_minor_version": OTBMAttributeReader.u32(attrs, 13),
        }

    @staticmethod
    def parse_map_attributes(attrs: bytes) -> Dict[str, str]:
        keys = {
            0x01: "description",
            0x0B: "spawn_file",
            0x0D: "house_file",
            0x17: "spawn_npc_file",
            0x18: "zone_file",
        }
        out: Dict[str, str] = {}
        offset = 0
        while offset + 3 <= len(attrs):
            attr_id = attrs[offset]
            size = OTBMAttributeReader.u16(attrs, offset + 1)
            offset += 3
            if offset + size > len(attrs):
                break
            key = keys.get(attr_id)
            if key:
                out[key] = attrs[offset : offset + size].decode("utf-8", errors="replace")
            offset += size
        return out

    @staticmethod
    def parse_tile_area(attrs: bytes) -> tuple[int, int, int]:
        if len(attrs) < 5:
            raise ValueError("tile area attrs too small")
        return (
            OTBMAttributeReader.u16(attrs, 0),
            OTBMAttributeReader.u16(attrs, 2),
            attrs[4],
        )

    @staticmethod
    def parse_tile(
        attrs: bytes,
        base_x: int,
        base_y: int,
        z: int,
        *,
        house: bool = False,
    ) -> Dict[str, Any]:
        minimum = 6 if house else 2
        if len(attrs) < minimum:
            raise ValueError("tile attrs too small")
        flags = 0
        ground = None
        offset = minimum
        while offset < len(attrs):
            attr = attrs[offset]
            offset += 1
            if attr == 0x03 and offset + 4 <= len(attrs):
                flags = OTBMAttributeReader.u32(attrs, offset)
                offset += 4
            elif attr == 0x09 and offset + 2 <= len(attrs):
                ground = OTBMAttributeReader.u16(attrs, offset)
                offset += 2
            else:
                break
        return {
            "x": base_x + attrs[0],
            "y": base_y + attrs[1],
            "z": z,
            "offset_x": attrs[0],
            "offset_y": attrs[1],
            "flags": flags,
            "house_id": OTBMAttributeReader.u32(attrs, 2) if house else None,
            "ground": ground,
            "items": [],
        }

    @staticmethod
    def parse_item(attrs: bytes) -> Dict[str, Any]:
        if len(attrs) < 2:
            raise ValueError("item attrs too small")
        item: Dict[str, Any] = {"id": OTBMAttributeReader.u16(attrs, 0), "attributes": {}}
        offset = 2
        while offset < len(attrs):
            attr = attrs[offset]
            offset += 1
            if attr in (0x0F, 0x11) and offset < len(attrs):
                value = attrs[offset]
                item["attributes"][attr] = value
                if attr == 0x0F:
                    item["count"] = value
                offset += 1
            elif attr in (0x04, 0x05, 0x0A, 0x16) and offset + 2 <= len(attrs):
                value = OTBMAttributeReader.u16(attrs, offset)
                item["attributes"][attr] = value
                key = {0x04: "action_id", 0x05: "unique_id", 0x0A: "depot_id", 0x16: "charges"}[attr]
                item[key] = value
                offset += 2
            elif attr == 0x0E and offset < len(attrs):
                item["house_door_id"] = attrs[offset]
                item["attributes"][attr] = attrs[offset]
                offset += 1
            elif attr == 0x08 and offset + 5 <= len(attrs):
                destination = {
                    "x": OTBMAttributeReader.u16(attrs, offset),
                    "y": OTBMAttributeReader.u16(attrs, offset + 2),
                    "z": attrs[offset + 4],
                }
                item["teleport_destination"] = destination
                item["attributes"][attr] = destination
                offset += 5
            elif attr == 0x10 and offset + 4 <= len(attrs):
                item["attributes"][attr] = OTBMAttributeReader.u32(attrs, offset)
                offset += 4
            elif attr in (0x06, 0x07, 0x13):
                text, offset = OTBMAttributeReader.string(attrs, offset)
                item["attributes"][attr] = text
                if attr == 0x06:
                    item["text"] = text
                elif attr == 0x07:
                    item["description"] = text
            else:
                break
        return item


class OTBMNodeReader:
    def __init__(self, source: str | Path | bytes):
        self.source = source
        self._fh = None
        self._mmap = None
        self._data: bytes | mmap.mmap
        if isinstance(source, (bytes, bytearray)):
            self._data = bytes(source)
            self.file_size = len(self._data)
            self.label = "bytes"
        else:
            self._data = b""
            self.file_size = 0
            self.label = str(source)

    def __enter__(self) -> "OTBMNodeReader":
        if isinstance(self.source, (bytes, bytearray)):
            return self
        path = Path(self.source)
        self._fh = path.open("rb")
        self.file_size = path.stat().st_size
        self._mmap = mmap.mmap(self._fh.fileno(), 0, access=mmap.ACCESS_READ)
        self._data = self._mmap
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._mmap is not None:
            self._mmap.close()
        if self._fh is not None:
            self._fh.close()

    def validate_header(self) -> None:
        if self.file_size < 6:
            raise ValueError("truncated OTBM data")
        if bytes(self._data[0:4]) not in OTBM_ACCEPTED_IDENTIFIERS:
            raise ValueError(f"invalid OTBM identifier: {bytes(self._data[0:4])!r}")
        if self._data[4] != RME_NODE_START:
            raise ValueError("root NODE_START not found at byte 4")

    def read_node(self, offset: int, depth: int = 0) -> OTBMNode:
        if offset >= self.file_size or self._data[offset] != RME_NODE_START:
            raise ValueError(f"expected NODE_START at offset {offset}")
        payload, delimiter, delimiter_offset, next_offset = self._read_payload(offset + 1)
        if not payload:
            raise ValueError(f"empty node payload at offset {offset}")
        return OTBMNode(
            node_type=payload[0],
            offset=offset,
            payload=payload,
            attrs=payload[1:],
            depth=depth,
            delimiter=delimiter,
            delimiter_offset=delimiter_offset,
            next_offset=next_offset,
        )

    def _read_payload(self, offset: int) -> tuple[bytes, int | None, int, int]:
        payload = bytearray()
        while offset < self.file_size:
            byte = self._data[offset]
            if byte in (RME_NODE_START, RME_NODE_END):
                return bytes(payload), byte, offset, offset + 1
            if byte == RME_ESCAPE:
                offset += 1
                if offset >= self.file_size:
                    raise ValueError("escape byte at end of data")
                payload.append(self._data[offset])
                offset += 1
                continue
            payload.append(byte)
            offset += 1
        return bytes(payload), None, self.file_size, self.file_size

    def skip_node(self, offset: int) -> int:
        if offset >= self.file_size or self._data[offset] != RME_NODE_START:
            raise ValueError(f"expected NODE_START at offset {offset}")
        cursor = offset
        depth = 0
        escaped = False
        while cursor < self.file_size:
            byte = self._data[cursor]
            if escaped:
                escaped = False
            elif byte == RME_ESCAPE:
                escaped = True
            elif byte == RME_NODE_START:
                depth += 1
            elif byte == RME_NODE_END:
                depth -= 1
                if depth == 0:
                    return cursor + 1
            cursor += 1
        raise ValueError(f"unterminated node at offset {offset}")

    def traverse(
        self,
        callback: Callable[[OTBMNode, dict[str, Any]], None],
        *,
        max_nodes: int | None = None,
        max_bytes: int | None = None,
    ) -> OTBMTraversalStats:
        self.validate_header()
        stats = OTBMTraversalStats()
        stop_at = self.file_size if max_bytes is None else min(self.file_size, max_bytes)
        context: dict[str, Any] = {}

        def walk(offset: int, depth: int) -> int:
            if offset >= stop_at:
                stats.truncated = True
                return offset
            if max_nodes is not None and stats.nodes_visited >= max_nodes:
                stats.truncated = True
                return offset
            node = self.read_node(offset, depth)
            stats.nodes_visited += 1
            stats.node_counts[node.name] = stats.node_counts.get(node.name, 0) + 1
            if node.node_type == 0x04:
                stats.tile_areas_detected += 1
                try:
                    _x, _y, z = OTBMAttributeReader.parse_tile_area(node.attrs)
                    stats.floors_detected.add(z)
                except ValueError as exc:
                    stats.diagnostics.append(str(exc))
            elif node.node_type in (0x05, 0x0E):
                stats.estimated_tiles += 1
            callback(node, context)
            if node.delimiter != RME_NODE_START:
                return node.next_offset
            cursor = node.delimiter_offset
            while cursor < stop_at:
                if cursor >= self.file_size:
                    return cursor
                byte = self._data[cursor]
                if byte == RME_NODE_START:
                    cursor = walk(cursor, depth + 1)
                    if stats.truncated:
                        return cursor
                    continue
                if byte == RME_NODE_END:
                    return cursor + 1
                raise ValueError(f"unexpected delimiter byte 0x{byte:02X} at offset {cursor}")
            stats.truncated = True
            return cursor

        walk(4, 0)
        return stats

    def build_index(self, *, max_nodes: int | None = None, max_bytes: int | None = None) -> OTBMSectionIndex:
        start = time.perf_counter()
        self.validate_header()
        root = self.read_node(4, 0)
        metadata = OTBMAttributeReader.parse_root(root.payload)
        if root.delimiter != RME_NODE_START:
            raise ValueError("root has no MAP_DATA child")
        map_node = self.read_node(root.delimiter_offset, 1)
        if map_node.node_type != 0x02:
            raise ValueError("MAP_DATA node not found")
        map_attrs = OTBMAttributeReader.parse_map_attributes(map_node.attrs)
        tile_areas: list[OTBMTileAreaIndex] = []
        area_stack: list[OTBMTileAreaIndex] = []

        def on_node(node: OTBMNode, _context: dict[str, Any]) -> None:
            if node.node_type == 0x04:
                try:
                    base_x, base_y, z = OTBMAttributeReader.parse_tile_area(node.attrs)
                except ValueError:
                    return
                area = OTBMTileAreaIndex(base_x, base_y, z, node.offset)
                tile_areas.append(area)
                area_stack[:] = [area]
            elif node.node_type in (0x05, 0x0E) and area_stack:
                area_stack[-1].estimated_tile_count += 1

        stats = self.traverse(on_node, max_nodes=max_nodes, max_bytes=max_bytes)
        if max_nodes is None and max_bytes is None:
            root_end = self.skip_node(4)
            if root_end != self.file_size:
                raise ValueError(f"unexpected trailing bytes after root node: {self.file_size - root_end}")
        return OTBMSectionIndex(
            metadata=metadata,
            map_attributes=map_attrs,
            tile_areas=tile_areas,
            stats=stats,
            file_size=self.file_size,
            elapsed_seconds=time.perf_counter() - start,
        )

    def extract_chunk(
        self,
        x: int,
        y: int,
        z: int,
        width: int,
        height: int,
        *,
        max_tiles: int = 4096,
        max_nodes: int | None = None,
        max_bytes: int | None = None,
    ) -> Dict[str, Any]:
        start = time.perf_counter()
        bounds = (x, y, x + width, y + height)
        tiles: list[dict[str, Any]] = []
        area_stack: list[tuple[int, int, int]] = []
        tile_stack: list[dict[str, Any] | None] = []
        item_stack: list[tuple[int, dict[str, Any]]] = []
        limit_reached = False

        def in_bounds(tile: dict[str, Any]) -> bool:
            return (
                bounds[0] <= tile["x"] < bounds[2]
                and bounds[1] <= tile["y"] < bounds[3]
                and tile["z"] == z
            )

        def on_node(node: OTBMNode, _context: dict[str, Any]) -> None:
            nonlocal limit_reached
            if node.node_type == 0x04:
                try:
                    area_stack[:] = [OTBMAttributeReader.parse_tile_area(node.attrs)]
                except ValueError:
                    area_stack.clear()
                tile_stack.clear()
                item_stack.clear()
            elif node.node_type in (0x05, 0x0E) and area_stack:
                base_x, base_y, base_z = area_stack[-1]
                try:
                    tile = OTBMAttributeReader.parse_tile(
                        node.attrs,
                        base_x,
                        base_y,
                        base_z,
                        house=node.node_type == 0x0E,
                    )
                except ValueError:
                    tile_stack[:] = [None]
                    return
                accepted = in_bounds(tile)
                if accepted and len(tiles) >= max_tiles:
                    limit_reached = True
                    accepted = False
                tile_stack[:] = [tile if accepted else None]
                item_stack.clear()
                if tile_stack[0] is not None:
                    tiles.append(tile_stack[0])
            elif node.node_type == 0x06 and tile_stack and tile_stack[-1] is not None:
                try:
                    item = OTBMAttributeReader.parse_item(node.attrs)
                except ValueError:
                    return
                tile = tile_stack[-1]
                if tile["ground"] is None:
                    tile["ground"] = item["id"]
                else:
                    while item_stack and item_stack[-1][0] >= node.depth:
                        item_stack.pop()
                    if item_stack and item_stack[-1][0] == node.depth - 1:
                        item_stack[-1][1].setdefault("children", []).append(item)
                    else:
                        tile["items"].append(item)
                    item_stack.append((node.depth, item))

        stats = self.traverse(on_node, max_nodes=max_nodes, max_bytes=max_bytes)
        truncated = stats.truncated or limit_reached
        return {
            "x": x,
            "y": y,
            "z": z,
            "width": width,
            "height": height,
            "tiles": tiles,
            "tile_count": len(tiles),
            "truncated": truncated,
            "stats": {
                "nodes_visited": stats.nodes_visited,
                "node_counts": stats.node_counts,
                "floors_detected": sorted(stats.floors_detected),
                "estimated_tiles": stats.estimated_tiles,
                "diagnostics": stats.diagnostics,
            },
            "elapsed_seconds": time.perf_counter() - start,
        }

    def extract_chunk_indexed(
        self,
        x: int,
        y: int,
        z: int,
        width: int,
        height: int,
        tile_areas: list[dict[str, Any]],
        *,
        max_tiles: int = 4096,
    ) -> Dict[str, Any]:
        """Extract a viewport by visiting only indexed 256x256 tile areas."""
        start = time.perf_counter()
        bounds = (x, y, x + width, y + height)
        tiles: list[dict[str, Any]] = []
        nodes_visited = 0
        limit_reached = False

        def overlaps(area: dict[str, Any]) -> bool:
            ax = int(area.get("base_x", 0))
            ay = int(area.get("base_y", 0))
            return (
                int(area.get("z", -1)) == z
                and ax < bounds[2]
                and ax + 256 > bounds[0]
                and ay < bounds[3]
                and ay + 256 > bounds[1]
            )

        def parse_item(offset: int, depth: int) -> dict[str, Any] | None:
            nonlocal nodes_visited
            node = self.read_node(offset, depth)
            nodes_visited += 1
            if node.node_type != 0x06:
                return None
            try:
                item = OTBMAttributeReader.parse_item(node.attrs)
            except ValueError:
                return None
            if node.delimiter == RME_NODE_START:
                cursor = node.delimiter_offset
                while cursor < self.file_size and self._data[cursor] != RME_NODE_END:
                    if self._data[cursor] != RME_NODE_START:
                        raise ValueError(f"unexpected item delimiter at offset {cursor}")
                    child = parse_item(cursor, depth + 1)
                    if child is not None:
                        item.setdefault("children", []).append(child)
                    cursor = self.skip_node(cursor)
            return item

        for area in (entry for entry in tile_areas if overlaps(entry)):
            area_offset = int(area.get("offset", -1))
            if area_offset < 0:
                continue
            area_node = self.read_node(area_offset, 2)
            nodes_visited += 1
            try:
                base_x, base_y, base_z = OTBMAttributeReader.parse_tile_area(area_node.attrs)
            except ValueError:
                continue
            if area_node.delimiter != RME_NODE_START:
                continue
            cursor = area_node.delimiter_offset
            while cursor < self.file_size and self._data[cursor] != RME_NODE_END:
                if self._data[cursor] != RME_NODE_START:
                    raise ValueError(f"unexpected tile delimiter at offset {cursor}")
                tile_node = self.read_node(cursor, 3)
                nodes_visited += 1
                if tile_node.node_type in (0x05, 0x0E):
                    try:
                        tile = OTBMAttributeReader.parse_tile(
                            tile_node.attrs,
                            base_x,
                            base_y,
                            base_z,
                            house=tile_node.node_type == 0x0E,
                        )
                    except ValueError:
                        tile = None
                    accepted = bool(
                        tile
                        and bounds[0] <= tile["x"] < bounds[2]
                        and bounds[1] <= tile["y"] < bounds[3]
                        and tile["z"] == z
                    )
                    if accepted and len(tiles) >= max_tiles:
                        accepted = False
                        limit_reached = True
                    if accepted and tile is not None:
                        if tile_node.delimiter == RME_NODE_START:
                            child_cursor = tile_node.delimiter_offset
                            while child_cursor < self.file_size and self._data[child_cursor] != RME_NODE_END:
                                if self._data[child_cursor] != RME_NODE_START:
                                    raise ValueError(f"unexpected tile child delimiter at offset {child_cursor}")
                                item = parse_item(child_cursor, 4)
                                if item is not None:
                                    if tile["ground"] is None:
                                        tile["ground"] = item["id"]
                                    else:
                                        tile["items"].append(item)
                                child_cursor = self.skip_node(child_cursor)
                        tiles.append(tile)
                cursor = self.skip_node(cursor)

        return {
            "x": x,
            "y": y,
            "z": z,
            "width": width,
            "height": height,
            "tiles": tiles,
            "tile_count": len(tiles),
            "truncated": limit_reached,
            "stats": {
                "nodes_visited": nodes_visited,
                "node_counts": {},
                "floors_detected": [z] if tiles else [],
                "estimated_tiles": len(tiles),
                "diagnostics": [],
            },
            "elapsed_seconds": time.perf_counter() - start,
        }


class OTBMImporter:
    """
    Main importer for converting .otbm files into WorldModel instances.

    Provides:
        - import_file(path) -> dict with WorldModel + stats
        - import_bytes(data) -> dict with WorldModel + stats
        - to_worldmodel(path) -> WorldModel instance
        - get_preview(path) -> summary of map contents
    """

    def __init__(self, validate: bool = True):
        """
        Args:
            validate: If True, run validator before parsing.
        """
        self._validator = OtbmValidator() if validate else None

    # ------------------------------------------------------------------
    # Main import methods
    # ------------------------------------------------------------------

    def import_file(self, file_path: str | Path) -> Dict[str, Any]:
        """
        Import an .otbm file and return a structured result.

        Args:
            file_path: Path to .otbm file.

        Returns:
            dict with keys:
                - "success": bool
                - "world_model": WorldModel instance (or None on failure)
                - "world_dict": WorldModel-compatible dict
                - "stats": dict of import statistics
                - "map_info": dict of map metadata
                - "errors": list of error messages (if any)
                - "warnings": list of warning messages (if any)
        """
        path = Path(file_path)
        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "stats": {},
                "map_info": {},
            }

        try:
            with path.open("rb") as fh:
                header = fh.read(6)
            if not self._is_rme_delimited_otbm(header):
                return {
                    "success": False,
                    "error": "Invalid Canary/RME OTBM header; expected 00000000 FE",
                    "stats": {},
                    "map_info": {},
                }
            return self._import_rme_delimited_file(path)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stats": {},
                "map_info": {},
            }

    def import_bytes(self, data: bytes, source: str = "bytes") -> Dict[str, Any]:
        """
        Import OTBM data from bytes.

        Args:
            data: Raw .otbm bytes.
            source: Optional source description (for error messages).

        Returns:
            dict with structured result (same keys as import_file).
        """
        errors: List[str] = []
        warnings: List[str] = []

        if not self._is_rme_delimited_otbm(data):
            return {
                "success": False,
                "error": "Invalid Canary/RME OTBM header; expected 00000000 FE",
                "stats": {},
                "map_info": {},
            }
        if self._validator:
            validation = self._validator.validate(data)
            if validation.status == "failure":
                return {
                    "success": False,
                    "error": f"Validation failed: {validation.errors}",
                    "stats": {},
                    "map_info": {},
                }
        return self._import_rme_delimited(data, source)

    def get_map_index(
        self,
        file_path: str | Path,
        *,
        max_nodes: int | None = None,
        max_bytes: int | None = None,
    ) -> Dict[str, Any]:
        with OTBMNodeReader(file_path) as reader:
            return reader.build_index(max_nodes=max_nodes, max_bytes=max_bytes).to_dict()

    def get_chunk(
        self,
        file_path: str | Path,
        x: int,
        y: int,
        z: int,
        width: int,
        height: int,
        *,
        max_tiles: int = 4096,
        max_nodes: int | None = None,
        max_bytes: int | None = None,
        tile_areas: list[dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        with OTBMNodeReader(file_path) as reader:
            if tile_areas:
                return reader.extract_chunk_indexed(
                    x,
                    y,
                    z,
                    width,
                    height,
                    tile_areas,
                    max_tiles=max_tiles,
                )
            return reader.extract_chunk(
                x,
                y,
                z,
                width,
                height,
                max_tiles=max_tiles,
                max_nodes=max_nodes,
                max_bytes=max_bytes,
            )

    def _import_rme_delimited_file(self, path: Path) -> Dict[str, Any]:
        try:
            with path.open("rb") as fh:
                identifier = fh.read(4).hex()
            with OTBMNodeReader(path) as reader:
                # The index drives lazy viewport loading and therefore must cover
                # the complete file. A bounded prefix is not a valid map index.
                index = reader.build_index()
        except Exception as exc:  # noqa: BLE001 - report parse failure as import failure
            return {
                "success": False,
                "error": f"RME OTBM traversal failed: {exc}",
                "stats": {},
                "map_info": {},
            }
        return self._result_from_rme_index(index, str(path), identifier=identifier)

    def _import_rme_delimited(self, data: bytes, source: str) -> Dict[str, Any]:
        """Import the real RME/Canary delimiter-based OTBM container.

        The canonical project contract is the four-zero identifier followed
        by the RME delimiter stream. Text-magic and size-prefixed synthetic
        nodes are intentionally rejected.
        """
        try:
            with OTBMNodeReader(data) as reader:
                index = reader.build_index()
        except Exception as exc:  # noqa: BLE001 - report parse failure as import failure
            return {
                "success": False,
                "error": f"RME OTBM inspection failed: {exc}",
                "stats": {},
                "map_info": {},
            }
        return self._result_from_rme_index(index, source, identifier=data[:4].hex())

    def _result_from_rme_index(self, index: OTBMSectionIndex, source: str, identifier: str) -> Dict[str, Any]:
        header = index.metadata
        if not header:
            return {
                "success": False,
                "error": "RME OTBM header not found",
                "stats": {},
                "map_info": {},
            }

        map_attributes = index.map_attributes
        cities: list[dict[str, Any]] = []
        waypoints: list[dict[str, Any]] = []
        sampled_tiles: list[dict[str, Any]] = []
        node_counts = index.stats.node_counts
        world_dict = {
            "version": header.get("version", 0),
            "width": header.get("width", 0),
            "height": header.get("height", 0),
            "item_major": header.get("item_major_version", 0),
            "item_minor": header.get("item_minor_version", 0),
            "description": map_attributes.get("description", ""),
            "spawn_file": map_attributes.get("spawn_file", ""),
            "spawn_npc_file": map_attributes.get("spawn_npc_file", ""),
            "house_file": map_attributes.get("house_file", ""),
            "zone_file": map_attributes.get("zone_file", ""),
            "tiles": sampled_tiles,
            "spawns": [],
            "cities": cities,
            "waypoints": waypoints,
            "tile_count": int(node_counts.get("TILE", index.stats.estimated_tiles)),
            "spawn_count": int(node_counts.get("SPAWN_AREA", 0)),
            "city_count": len(cities),
            "waypoint_count": len(waypoints),
            "rme_import_mode": "indexed",
            "parse_truncated": bool(index.stats.truncated),
            "index": index.to_dict(),
        }
        world_model = self._worldmodel_from_dict(world_dict)
        map_info = {
            "version": world_dict["version"],
            "width": world_dict["width"],
            "height": world_dict["height"],
            "item_major": world_dict["item_major"],
            "item_minor": world_dict["item_minor"],
            "description": world_dict["description"],
            "spawn_file": world_dict["spawn_file"],
            "spawn_npc_file": world_dict["spawn_npc_file"],
            "house_file": world_dict["house_file"],
            "zone_file": world_dict["zone_file"],
        }
        stats = {
            "tiles": world_dict["tile_count"],
            "spawns": world_dict["spawn_count"],
            "cities": world_dict["city_count"],
            "waypoints": world_dict["waypoint_count"],
            "file_size": index.file_size,
            "source": source,
            "identifier": identifier,
            "root_marker": RME_NODE_START,
            "root_type": header.get("root_payload_type"),
            "node_counts": node_counts,
            "parse_truncated": index.stats.truncated,
            "parse_node_limit": index.stats.nodes_visited,
            "tile_areas": len(index.tile_areas),
            "floors_detected": sorted(index.stats.floors_detected),
            "index_elapsed_seconds": index.elapsed_seconds,
        }
        if index.stats.truncated:
            return {
                "success": False,
                "error": "RME OTBM full-file index is incomplete",
                "stats": stats,
                "map_info": map_info,
                "errors": ["A partial index cannot safely drive viewport editing or export."],
                "warnings": [],
            }
        warnings = []
        return {
            "success": True,
            "world_model": world_model,
            "world_dict": world_dict,
            "stats": stats,
            "map_info": map_info,
            "errors": [],
            "warnings": warnings,
            "rme_report": {
                "header_fields": header,
                "map_attributes": map_attributes,
                "node_counts": node_counts,
                "tile_areas": [area.__dict__ for area in index.tile_areas[:32]],
                "floors_detected": sorted(index.stats.floors_detected),
                "diagnostics": index.stats.diagnostics,
            },
        }

    @staticmethod
    def _is_rme_delimited_otbm(data: bytes) -> bool:
        return (
            len(data) >= 6
            and data[:4] in OTBM_ACCEPTED_IDENTIFIERS
            and data[4] == RME_NODE_START
        )

    @staticmethod
    def _worldmodel_from_dict(world_dict: Dict[str, Any]) -> Any:
        from core.world_engine.world_engine import WorldModel

        world_model = WorldModel()
        for city in world_dict.get("cities", []) or []:
            world_model.add_city(city)
        for spawn in world_dict.get("spawns", []) or []:
            world_model.add_spawn(spawn)
        world_model.waypoints.extend(world_dict.get("waypoints", []) or [])
        return world_model

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    def to_worldmodel(self, file_path: str | Path) -> Any:
        """
        Import an .otbm file and return a WorldModel instance directly.

        Args:
            file_path: Path to .otbm file.

        Returns:
            WorldModel instance.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            OtbmParseError: If parsing fails.
            WorldBuildError: If building the WorldModel fails.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"OTBM file not found: {file_path}")

        result = self.import_file(path)
        if not result.get("success"):
            raise OtbmParseError(str(result.get("error", "OTBM import failed")))
        return result["world_model"]

    def to_worldmodel_from_bytes(self, data: bytes) -> Any:
        """
        Import OTBM from bytes and return a WorldModel instance.

        Args:
            data: Raw .otbm bytes.

        Returns:
            WorldModel instance.

        Raises:
            OtbmParseError: If parsing fails.
        """
        result = self.import_bytes(data)
        if not result.get("success"):
            raise OtbmParseError(str(result.get("error", "OTBM import failed")))
        return result["world_model"]

    def get_preview(self, file_path: str | Path) -> Dict[str, Any]:
        """
        Get a summary preview of an OTBM map without full import.

        Args:
            file_path: Path to .otbm file.

        Returns:
            dict with preview info: version, dimensions, tile/spawn/city/waypoint counts.
        """
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}"}

        data = path.read_bytes()
        return self.get_preview_from_bytes(data)

    def get_preview_from_bytes(self, data: bytes) -> Dict[str, Any]:
        """
        Get a summary preview of OTBM data without full import.

        Args:
            data: Raw .otbm bytes.

        Returns:
            dict with preview info.
        """
        result = self.import_bytes(data, source="preview")
        if not result.get("success"):
            return {"valid": False, "error": result.get("error", "invalid OTBM"), "file_size": len(data)}
        info = result["map_info"]
        stats = result["stats"]
        return {
            "valid": True,
            "version": info.get("version", 0),
            "width": info.get("width", 0),
            "height": info.get("height", 0),
            "item_major": info.get("item_major", 0),
            "item_minor": info.get("item_minor", 0),
            "file_size": len(data),
            "tile_areas": stats.get("tile_areas", 0),
            "tiles": stats.get("tiles", 0),
            "spawns": stats.get("spawns", 0),
            "towns": stats.get("cities", 0),
            "waypoints": stats.get("waypoints", 0),
        }

    # ------------------------------------------------------------------
    # Round trip: import then re-export
    # ------------------------------------------------------------------

    def round_trip(
        self, file_path: str | Path, output_path: Optional[str | Path] = None
    ) -> Dict[str, Any]:
        """
        Perform a full round trip: import OTBM -> WorldModel -> export OTBM.

        This verifies that the import/export pipeline is lossless for the
        structural data (tiles, spawns, towns, waypoints).

        Args:
            file_path: Source .otbm file to import.
            output_path: Optional path to write the re-exported .otbm file.

        Returns:
            dict with round trip results:
                - "import_success": bool
                - "export_success": bool
                - "import_stats": dict
                - "export_stats": dict
                - "original_size": int
                - "exported_size": int
                - "tiles_match": bool (count only)
                - "spawns_match": bool (count only)
        """
        from core.otbm.otbm_serializer import OtbmSerializer

        # Import
        source_data = Path(file_path).read_bytes()
        import_result = self.import_bytes(source_data)

        if not import_result.get("success"):
            return {
                "import_success": False,
                "error": import_result.get("error", "Import failed"),
            }

        world_model = import_result.get("world_model")

        # Export
        serializer = OtbmSerializer()
        try:
            exported_data = serializer.serialize(world_model)
            export_success = True
        except Exception as e:
            export_success = False
            exported_data = b""
            export_error = str(e)

        result = {
            "import_success": True,
            "export_success": export_success,
            "import_stats": import_result.get("stats", {}),
            "original_size": len(source_data),
            "exported_size": len(exported_data) if exported_data else 0,
            "tiles_match": (
                (
                    import_result.get("stats", {}).get("tiles", 0)
                    == self._count_tiles_in_bytes(exported_data)
                )
                if exported_data
                else False
            ),
            "spawns_match": (
                (
                    import_result.get("stats", {}).get("spawns", 0)
                    == self._count_spawns_in_bytes(exported_data)
                )
                if exported_data
                else False
            ),
        }

        if not export_success:
            result["export_error"] = export_error

        # Optionally write output
        if output_path and exported_data:
            Path(output_path).write_bytes(exported_data)
            result["output_path"] = str(output_path)

        return result

    @staticmethod
    def _count_tiles_in_bytes(data: bytes) -> int:
        """Quick count of TILE nodes in exported bytes."""
        if not data:
            return 0
        from .node_encoder import OTBM_NODE_TILE

        count = 0
        offset = 0
        while offset < len(data):
            # Search for TILE node marker
            idx = data.find(bytes([OTBM_NODE_TILE]), offset)
            if idx == -1:
                break
            count += 1
            offset = idx + 1
        return count

    @staticmethod
    def _count_spawns_in_bytes(data: bytes) -> int:
        """Quick count of MONSTER nodes in exported bytes."""
        if not data:
            return 0
        from .node_encoder import OTBM_NODE_MONSTER

        count = 0
        offset = 0
        while offset < len(data):
            idx = data.find(bytes([OTBM_NODE_MONSTER]), offset)
            if idx == -1:
                break
            count += 1
            offset = idx + 1
        return count
