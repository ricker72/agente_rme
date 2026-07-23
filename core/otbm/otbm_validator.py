from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import List

from .compatibility.otbm_constants import (
    OTBM_ACCEPTED_IDENTIFIERS,
    OTBM_ROOTV1 as OTBM_NODE_ROOT,
    OTBM_MAP_DATA,
    OTBM_TILE_AREA,
    OTBM_TILE,
    OTBM_ITEM,
    OTBM_SPAWNS,
    OTBM_SPAWN_AREA,
    OTBM_MONSTER,
    OTBM_TOWNS,
    OTBM_TOWN,
    OTBM_WAYPOINTS,
    OTBM_WAYPOINT,
    OTBM_ATTR_DESCRIPTION,
    OTBM_ATTR_EXT_FILE,
    OTBM_ATTR_TILE_FLAGS,
    OTBM_ATTR_ACTION_ID,
    OTBM_ATTR_UNIQUE_ID,
    OTBM_ATTR_TEXT,
    OTBM_ATTR_DESC,
    OTBM_ATTR_COUNT,
    OTBM_ATTR_SUBTYPE,
    OTBM_ATTR_DURATION,
    OTBM_ATTR_DECAYING_STATE,
    OTBM_ATTR_WRITTENDATE,
    OTBM_ATTR_WRITTENBY,
    OTBM_ATTR_SLEEPERGUID,
    OTBM_ATTR_SLEEPSTART,
    OTBM_ATTR_CHARGES,
    OTBM_ATTR_EXT_SPAWN_MONSTER_FILE,
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

    OTBM_MAGIC = b"\x00\x00\x00\x00"
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
        # Import NodeEncoder locally to avoid circular imports
        from .node_encoder import NodeEncoder

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
        return self._validate_rme_tree(data)

    def _validate_rme_tree(self, data: bytes) -> OtbmValidationResult:
        """Validate the only supported stream: wildcard identifier + FE/FF tree."""
        report = OtbmValidationResult(stats={"file_size": len(data)})
        if len(data) < 6:
            report.status = "failure"
            report.errors.append("Empty or truncated Canary/RME OTBM data")
            return report
        if data[:4] not in OTBM_ACCEPTED_IDENTIFIERS or data[4] != 0xFE:
            report.status = "failure"
            report.errors.append("Invalid Canary/RME OTBM header; expected 00000000 FE or OTBM FE")
            return report
        try:
            from .otbm_importer import OTBMNodeReader

            with OTBMNodeReader(data) as reader:
                index = reader.build_index(max_nodes=None, max_bytes=None)
        except Exception as exc:  # noqa: BLE001 - malformed input must fail closed
            report.status = "failure"
            report.errors.append(f"Malformed Canary/RME OTBM tree: {exc}")
            return report
        if index.stats.truncated:
            report.status = "failure"
            report.errors.append("Canary/RME OTBM traversal was truncated")
            return report
        report.stats.update({
            "version": index.metadata.get("version", 0),
            "width": index.metadata.get("width", 0),
            "height": index.metadata.get("height", 0),
            "item_version": (
                f"{index.metadata.get('item_major_version', 0)}."
                f"{index.metadata.get('item_minor_version', 0)}"
            ),
            "total_nodes": index.stats.nodes_visited,
            "tiles": index.stats.estimated_tiles,
            "items": index.stats.node_counts.get("ITEM", 0),
            "spawn_areas": index.stats.node_counts.get("SPAWN_AREA", 0),
            "monsters": index.stats.node_counts.get("MONSTER", 0),
            "towns": index.stats.node_counts.get("TOWN", 0),
            "waypoints": index.stats.node_counts.get("WAYPOINT", 0),
            "tile_areas": index.stats.tile_areas_detected,
        })
        if report.stats["width"] <= 0 or report.stats["height"] <= 0:
            report.status = "failure"
            report.errors.append("Map dimensions must be positive")
        return report

    def _validate_legacy_size_prefixed_stream(self, data: bytes) -> OtbmValidationResult:
        """Removed runtime path retained temporarily for source-history readability."""
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

        if data[:4] not in OTBM_ACCEPTED_IDENTIFIERS:
            report.status = "failure"
            report.errors.append(
                f"Invalid OTBM magic identifier: got {data[:4]!r}"
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

        # v1.0.1 HOTFIX: the root header actually consumes 4+2+2+4+4 = 16
        # bytes (version + width + height + item_major + item_minor). The
        # previous check used 14 which was off-by-two and caused a
        # ``struct.error`` to leak out of ``validate()`` on truncated
        # inputs (clis crashed with a traceback on corrupt OTBM files).
        if end_root - offset < 16:
            report.errors.append("Root node too small for header attributes")
            report.status = "failure"
            return report

        try:
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
        except (struct.error, IndexError) as e:
            # v1.0.1 HOTFIX: never let a malformed input leak a
            # ``struct.error`` out of the validator; instead mark the
            # report as failed and stop.
            report.errors.append(
                f"Validation error: failed to read root header at offset {offset}: {e}"
            )
            report.status = "failure"
            return report

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
                report.errors.append(
                    f"Node 0x{node_type:02X} at offset {offset - 3} extends beyond parent"
                )
                report.status = "failure"
                child_end = end
            self.stats["total_nodes"] += 1
            self._validate_node(data, offset, child_end, node_type, report, context)
            offset = child_end
        return offset

    def _validate_node(self, data, offset, end, node_type, report, context):
        if node_type == OTBM_MAP_DATA:
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
        elif node_type == OTBM_TILE_AREA:
            if end - offset >= 5:
                offset += 5
            self._validate_children(data, offset, end, report, "TILE_AREA")
        elif node_type == OTBM_TILE:
            if end - offset < 2:
                report.errors.append(f"TILE node too small at offset {offset - 3}")
                report.status = "failure"
                return
            off_x = data[offset]
            off_y = data[offset + 1]
            offset += 2
            if offset < end and data[offset] == OTBM_ATTR_TILE_FLAGS:
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
        elif node_type == OTBM_ITEM:
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
                report.warnings.append(
                    f"Item ID 0 (empty) at offset {offset - 5} - this may cause issues in RME"
                )
            while offset < end:
                if offset >= end:
                    break
                attr = data[offset]
                offset += 1
                if attr == OTBM_ATTR_DESCRIPTION:
                    if offset + 2 > end:
                        break
                    slen = struct.unpack_from("<H", data, offset)[0]
                    offset += 2 + slen
                elif attr in (
                    OTBM_ATTR_EXT_FILE,
                    OTBM_ATTR_EXT_SPAWN_MONSTER_FILE,
                ):
                    if offset + 2 > end:
                        break
                    slen = struct.unpack_from("<H", data, offset)[0]
                    offset += 2 + slen
                elif attr == OTBM_ATTR_ACTION_ID:
                    offset += 2
                elif attr == OTBM_ATTR_UNIQUE_ID:
                    offset += 2
                elif attr == OTBM_ATTR_TEXT:
                    if offset + 2 > end:
                        break
                    slen = struct.unpack_from("<H", data, offset)[0]
                    offset += 2 + slen
                elif attr == OTBM_ATTR_DESC:
                    if offset + 2 > end:
                        break
                    slen = struct.unpack_from("<H", data, offset)[0]
                    offset += 2 + slen
                elif attr in (
                    OTBM_ATTR_COUNT,
                    OTBM_ATTR_SUBTYPE,
                    OTBM_ATTR_DECAYING_STATE,
                    OTBM_ATTR_CHARGES,
                ):
                    offset += 1
                elif attr in (
                    OTBM_ATTR_DURATION,
                    OTBM_ATTR_WRITTENDATE,
                    OTBM_ATTR_SLEEPERGUID,
                    OTBM_ATTR_SLEEPSTART,
                ):
                    offset += 4
                elif attr == OTBM_ATTR_WRITTENBY:
                    if offset + 2 > end:
                        break
                    slen = struct.unpack_from("<H", data, offset)[0]
                    offset += 2 + slen
                elif attr == OTBM_ITEM:
                    break
                else:
                    break
            if offset < end:
                self._validate_children(data, offset, end, report, f"ITEM({item_id})")
        elif node_type == OTBM_SPAWNS:
            self._validate_children(data, offset, end, report, "SPAWNS")
        elif node_type == OTBM_SPAWN_AREA:
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
        elif node_type == OTBM_MONSTER:
            if end - offset >= 2:
                mlen = struct.unpack_from("<H", data, offset)[0]
                offset += 2 + mlen
                if offset + 5 <= end:
                    offset += 5
            self.stats["monsters"] += 1
        elif node_type == OTBM_TOWNS:
            self._validate_children(data, offset, end, report, "TOWNS")
        elif node_type == OTBM_TOWN:
            if end - offset >= 4:
                _ = struct.unpack_from("<I", data, offset)[0]
                offset += 4
                if offset + 2 <= end:
                    tlen = struct.unpack_from("<H", data, offset)[0]
                    offset += 2 + tlen
                    if offset + 5 <= end:
                        offset += 5
            self.stats["towns"] += 1
        elif node_type == OTBM_WAYPOINTS:
            self._validate_children(data, offset, end, report, "WAYPOINTS")
        elif node_type == OTBM_WAYPOINT:
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
