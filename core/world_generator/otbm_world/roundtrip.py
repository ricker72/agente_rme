from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Dict, List

from .escape import ESCAPE_BYTE, NODE_END, NODE_START
from .fingerprint import sha256_fingerprint
from .header import OTBM_MAGIC


@dataclass(frozen=True)
class RoundtripResult:
    valid: bool
    width: int
    height: int
    tile_count: int
    item_count: int
    node_ordering_valid: bool
    fingerprint: str
    errors: tuple[str, ...] = ()

    def to_json_dict(self) -> Dict[str, object]:
        return {
            "valid": self.valid,
            "width": self.width,
            "height": self.height,
            "tile_count": self.tile_count,
            "item_count": self.item_count,
            "node_ordering_valid": self.node_ordering_valid,
            "fingerprint": self.fingerprint,
            "errors": list(self.errors),
        }


def read_otbm_summary(data: bytes) -> RoundtripResult:
    errors: List[str] = []
    if not data.startswith(OTBM_MAGIC):
        errors.append("missing OTBM magic")
        return RoundtripResult(False, 0, 0, 0, 0, False, sha256_fingerprint(data), tuple(errors))

    width = height = 0
    tile_count = 0
    item_count = 0
    stack: List[int] = []
    root_seen = False
    map_data_seen = False
    ordering_valid = True
    i = len(OTBM_MAGIC)
    while i < len(data):
        byte = data[i]
        if byte == ESCAPE_BYTE:
            i += 2
            continue
        if byte == NODE_START:
            if i + 1 >= len(data):
                errors.append("truncated node start")
                break
            node_type = data[i + 1]
            if not stack and node_type != 0x00:
                ordering_valid = False
            if node_type == 0x02 and (not stack or stack[-1] != 0x00):
                ordering_valid = False
            if node_type in (0x05, 0x0E) and (not stack or stack[-1] != 0x04):
                ordering_valid = False
            if node_type == 0x06 and (not stack or stack[-1] not in (0x05, 0x0E, 0x06)):
                ordering_valid = False
            stack.append(node_type)
            if node_type == 0x00:
                root_seen = True
                if i + 18 <= len(data):
                    _, width, height, _, _ = struct.unpack("<IHHII", data[i + 2 : i + 18])
                i += 18
                continue
            if node_type == 0x02:
                map_data_seen = True
            elif node_type in (0x05, 0x0E):
                tile_count += 1
            elif node_type == 0x06:
                item_count += 1
            i += 2
            continue
        if byte == NODE_END:
            if stack:
                stack.pop()
            else:
                ordering_valid = False
            i += 1
            continue
        i += 1

    if stack:
        errors.append("unclosed OTBM nodes")
    if not root_seen:
        errors.append("missing root node")
    if not map_data_seen:
        errors.append("missing map data node")
    if tile_count <= 0:
        errors.append("no tiles serialized")
    return RoundtripResult(
        valid=not errors and ordering_valid,
        width=width,
        height=height,
        tile_count=tile_count,
        item_count=item_count,
        node_ordering_valid=ordering_valid,
        fingerprint=sha256_fingerprint(data),
        errors=tuple(errors),
    )
