from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import List, Optional

from .node_encoder import (
    NodeEncoder,
    OTBM_NODE_ROOT,
    OTBM_NODE_MAP_DATA,
    OTBM_NODE_TILE_AREA,
    OTBM_NODE_TILE,
    OTBM_NODE_ITEM,
    OTBM_NODE_SPAWNS,
    OTBM_NODE_SPAWN_AREA,
    OTBM_NODE_MONSTER,
    OTBM_NODE_TOWNS,
    OTBM_NODE_TOWN,
    OTBM_NODE_WAYPOINTS,
    OTBM_NODE_WAYPOINT,
    TILESTATE_PROTECTIONZONE,
    TILESTATE_NOPVPZONE,
    TILESTATE_NOLOGOUT,
    TILESTATE_PVPZONE,
    TILESTATE_REFRESH,
    TILESTATE_TRASHED,
)


@dataclass
class OtbmValidationResult:
    status: str = "success"  # "success" or "failure"
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        return self.status == "success"


class OtbmValidator:
    """Validates OTBM binary data for OpenTibiaBR / RME compatibility."""

    OTBM_MAGIC = b"OTBM"
    MAX_ITEM_ID = 65535
    MIN_ITEM_ID = 0
    MAX_MAP_DIM = 65535
    VALID_TILE_FLAGS = (
        TILESTATE_PROTECTIONZONE
        | TILESTATE_NOPVPZONE
        | TILESTATE_NOLOGOUT
        | TILESTATE_PVPZONE
        | TILESTATE_REFRESH
        | TILESTATE_TRASHED
    )

    def __init__(self):
        self.node = NodeEncoder()
        # HITO 26.1A — own a ByteValidator for post-write byte checks
        from .byte_validator import ByteValidator
        self.byte_validator = ByteValidator()
        self.stats = {
            "total_nodes": 0,
            "tiles": 0,
            "items": 0,
            "spawn_areas": 0,
            "monsters": 0,
            "towns": 0,
            "waypoints": 0,
        }

    def validate(self, data: bytes) -> OtbmValidationResult:
        self.stats = {
            "total_nodes": 0,
            "tiles": 0,
            "items": 0,
            "spawn_areas": 0,
            "monsters": 0,
            "towns": 0,
            "waypoints": 0,
            "file_size": len(data),
        }
        report = OtbmValidationResult(stats=self.stats)

        if not data or len(data) < 4:
            report.status = "failure"
            report.errors.append("Empty or truncated OTBM data (no magic identifier)")
            return report

        if data[:4] != self.OTBM_MAGIC:
            report.status = "failure"
            report.errors.append(
                f"Invalid OTBM magic identifier: expected {self.OTBM_MAGIC!r}, got {data[:4]!r}"
            )
            return report

        offset = 4
        if offset >= len(data):
            report.status = "failure"
            report.errors.append("Truncated data: no root node type byte")
            return report

        node_type = data[offset]
        offset += 1
        if node_type != OTBM_NODE_ROOT:
            report.errors.append(
                f"Expected ROOT node (0x{OTBM_NODE_ROOT:02X}), got 0x{node_type:02X}"
            )
            report.status = "failure"

        end_root = len(data)

        if end_root - offset < 14:
            report.errors.append("Root node too small for header attributes")
            report.status = "failure"
            return report

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

        self.stats["version"] = version
        self.stats["width"] = width
        self.stats["height"] = height
        self.stats["item_version"] = f"{item_major}.{item_minor}"

        if width == 0 or height == 0:
            report.warnings.append("Map dimensions are zero: map may be empty")
        if width > self.MAX_MAP_DIM or height > self.MAX_MAP_DIM:
            report.errors.append(
                f"Map dimensions ({width}x{height}) exceed maximum ({self.MAX_MAP_DIM})"
            )
            report.status = "failure"

        try:
            offset = self._validate_children(data, offset, end_root, report, context="ROOT")
        except Exception as e:
            report.errors.append(f"Validation error at offset {offset}: {e}")
            report.status = "failure"

        if self.stats["tiles"] == 0 and self.stats["monsters"] == 0:
            report.warnings.append("Map contains no tiles or monsters")

        if self.stats["tiles"] > 0 and self.stats["items"] == 0:
            report.warnings.append("Tiles present but no items found (may be missing ground items)")

        report.stats = self.stats
        return report

    def _validate_children(self, data, offset, end, report, context):
        while offset < end:
            if offset + 3 > len(data):
                report.errors.append(f"Truncated node header at offset {offset} in {context}")
                report.status = "failure"
                break
            node_type = data[offset]
            child_size = struct.unpack_from("<H", data, offset + 1)[0]
            offset += 3
            child_end = offset + child_size
            if child_end > end and end < len(data):
                report.errors.append(f"Node 0x{node_type:02X} at offset {offset - 3} extends beyond parent")
                report.status = "failure"
                child_end = end
            self.stats["total_nodes"] += 1
            self._validate_node(data, offset, child_end, node_type, report, context)
            offset = child_end
        return offset

    def _validate_node(self, data, offset, end, node_type, report, context):
        if node_type == OTBM_NODE_MAP_DATA:
            if end - offset >= 2:
                desc_len = struct.unpack_from("<H", data, offset)[0]
                offset += 2 + desc_len
                if offset + 2 <= end:
                    spawn_len = struct.unpack_from("<H", data, offset)[0]
                    offset += 2 + spawn_len
                    if offset + 2 <= end:
                        house_len = struct.unpack_from("<H", data, offset)[0]
                        offset += 2 + house_len
            self._validate_children(data, offset, end, report, "MAP_DATA")
        elif node_type == OTBM_NODE_TILE_AREA:
            if end - offset >= 5:
                offset += 5
            self._validate_children(data, offset, end, report, "TILE_AREA")
        elif node_type == OTBM_NODE_TILE:
            if end - offset < 2:
                report.errors.append(f"TILE node too small at offset {offset - 3}")
                report.status = "failure"
                return
            off_x = data[offset]
            off_y = data[offset + 1]
            offset += 2
            if offset < end and data[offset] == 0x04:
                if offset + 3 <= end:
                    child_size = struct.unpack_from("<H", data, offset + 1)[0]
                    if offset + 3 + child_size <= end and child_size >= 2:
                        pass
                    elif offset + 5 <= end:
                        offset += 1
                        flags = struct.unpack_from("<I", data, offset)[0]
                        offset += 4
                        invalid_flags = flags & ~self.VALID_TILE_FLAGS
                        if invalid_flags:
                            report.warnings.append(
                                f"Unknown tile flags 0x{invalid_flags:08X} on tile at ({off_x}, {off_y})"
                            )
            self.stats["tiles"] += 1
            self._validate_children(data, offset, end, report, f"TILE({off_x},{off_y})")
        elif node_type == OTBM_NODE_ITEM:
            if end - offset < 2:
                report.errors.append(f"ITEM node too small at offset {offset - 3}")
                report.status = "failure"
                return
            item_id = struct.unpack_from("<H", data, offset)[0]
            offset += 2
            self.stats["items"] += 1
            if item_id > self.MAX_ITEM_ID:
                report.warnings.append(f"Item ID {item_id} exceeds 65535 at offset {offset - 5}")
            if item_id == 0:
                report.warnings.append(f"Item ID 0 (empty) at offset {offset - 5} - this may cause issues in RME")
            while offset < end:
                if offset >= end:
                    break
                attr = data[offset]
                offset += 1
                if attr == 0x01:
                    if offset + 2 > end:
                        break
                    slen = struct.unpack_from("<H", data, offset)[0]
                    offset += 2 + slen
                elif attr in (0x02, 0x03, 0x0B):
                    if offset + 2 > end:
                        break
                    slen = struct.unpack_from("<H", data, offset)[0]
                    offset += 2 + slen
                elif attr == 0x04:
                    break
                elif attr in (0x07, 0x08):
                    offset += 2
                elif attr in (0x0A, 0x0F):
                    if offset + 2 > end:
                        break
                    slen = struct.unpack_from("<H", data, offset)[0]
                    offset += 2 + slen
                elif attr in (0x0C, 0x0E, 0x10, 0x11):
                    offset += 4
                elif attr in (0x05, 0x06, 0x0D, 0x12, 0x13):
                    offset += 1
                else:
                    break
            if offset < end:
                self._validate_children(data, offset, end, report, f"ITEM({item_id})")
        elif node_type == OTBM_NODE_SPAWNS:
            self._validate_children(data, offset, end, report, "SPAWNS")
        elif node_type == OTBM_NODE_SPAWN_AREA:
            if end - offset >= 6:
                _ = struct.unpack_from("<H", data, offset)[0]
                offset += 2
                _ = struct.unpack_from("<H", data, offset)[0]
                offset += 2
                _ = data[offset]
                offset += 1
                _ = data[offset]
                offset += 1
            self.stats["spawn_areas"] += 1
            self._validate_children(data, offset, end, report, "SPAWN_AREA")
        elif node_type == OTBM_NODE_MONSTER:
            if end - offset >= 2:
                mlen = struct.unpack_from("<H", data, offset)[0]
                offset += 2 + mlen
                if offset + 5 <= end:
                    offset += 5
            self.stats["monsters"] += 1
        elif node_type == OTBM_NODE_TOWNS:
            self._validate_children(data, offset, end, report, "TOWNS")
        elif node_type == OTBM_NODE_TOWN:
            if end - offset >= 4:
                _ = struct.unpack_from("<I", data, offset)[0]
                offset += 4
                if offset + 2 <= end:
                    tlen = struct.unpack_from("<H", data, offset)[0]
                    offset += 2 + tlen
                    if offset + 5 <= end:
                        offset += 5
            self.stats["towns"] += 1
        elif node_type == OTBM_NODE_WAYPOINTS:
            self._validate_children(data, offset, end, report, "WAYPOINTS")
        elif node_type == OTBM_NODE_WAYPOINT:
            if end - offset >= 2:
                wlen = struct.unpack_from("<H", data, offset)[0]
                offset += 2 + wlen
                if offset + 5 <= end:
                    offset += 5
            self.stats["waypoints"] += 1

    def validate_world_model(self, world_model) -> OtbmValidationResult:
        report = OtbmValidationResult(stats={"pre_serialize": True})
        tiles = getattr(world_model, "tiles", {}) or {}
        if not tiles:
            report.warnings.append("WorldModel has no tiles")
        for key, tile in tiles.items():
            x = getattr(tile, "x", None) or (tile.get("x") if isinstance(tile, dict) else 0)
            y = getattr(tile, "y", None) or (tile.get("y") if isinstance(tile, dict) else 0)
            z = getattr(tile, "z", None) or (tile.get("z") if isinstance(tile, dict) else 0)
            if x is None or y is None or z is None:
                report.errors.append(f"Tile {key} missing coordinates")
                report.status = "failure"
            if isinstance(x, (int, float)) and x > self.MAX_MAP_DIM:
                report.errors.append(f"Tile {key} x={x} exceeds max dimension")
                report.status = "failure"
            if isinstance(y, (int, float)) and y > self.MAX_MAP_DIM:
                report.errors.append(f"Tile {key} y={y} exceeds max dimension")
                report.status = "failure"
        spawns = getattr(world_model, "spawns", []) or []
        for i, spawn in enumerate(spawns):
            if isinstance(spawn, dict) and not spawn.get("monster") and not spawn.get("name"):
                report.warnings.append(f"Spawn [{i}] has no monster name")
        report.stats["tile_count"] = len(tiles)
        report.stats["spawn_count"] = len(spawns)
        return report
