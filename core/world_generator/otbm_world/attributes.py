from __future__ import annotations

import struct
from typing import Any, Mapping

ATTR_DESCRIPTION = 0x01
ATTR_TILE_FLAGS = 0x03
ATTR_ACTION_ID = 0x04
ATTR_UNIQUE_ID = 0x05
ATTR_TEXT = 0x06
ATTR_DESC = 0x07
ATTR_TELE_DEST = 0x08
ATTR_DEPOT_ID = 0x0A
ATTR_HOUSE_DOOR_ID = 0x0E
ATTR_COUNT = 0x0F
ATTR_CHARGES = 0x16


def write_string(value: str) -> bytes:
    encoded = (value or "").encode("utf-8", errors="ignore")[:65535]
    return struct.pack("<H", len(encoded)) + encoded


def _u16(value: Any) -> bytes:
    return struct.pack("<H", max(0, min(0xFFFF, int(value))))


def _u32(value: Any) -> bytes:
    return struct.pack("<I", max(0, min(0xFFFFFFFF, int(value))))


def encode_supported_attributes(attributes: Mapping[str, Any]) -> bytes:
    out = bytearray()
    for key in sorted(attributes):
        value = attributes[key]
        if value is None:
            continue
        if key == "action_id":
            out.append(ATTR_ACTION_ID)
            out.extend(_u16_checked("action_id", value))
        elif key == "depot_id":
            out.append(ATTR_DEPOT_ID)
            out.extend(_u16_checked("depot_id", value))
        elif key == "house_door_id":
            out.append(ATTR_HOUSE_DOOR_ID)
            out.append(_checked_int("house_door_id", value, 0xFF))
        elif key == "teleport_destination":
            destination = dict(value)
            out.append(ATTR_TELE_DEST)
            out.extend(_u16_checked("teleport x", destination["x"]))
            out.extend(_u16_checked("teleport y", destination["y"]))
            out.append(_checked_int("teleport z", destination["z"], 0xFF))
        elif key == "count":
            out.append(ATTR_COUNT)
            out.append(_checked_int("count", value, 0xFF))
        elif key == "charges":
            out.append(ATTR_CHARGES)
            out.extend(_u16_checked("charges", value))
        elif key == "description":
            out.append(ATTR_DESC)
            out.extend(write_string(str(value)))
        elif key == "text":
            out.append(ATTR_TEXT)
            out.extend(write_string(str(value)))
        elif key == "tile_flags":
            out.append(ATTR_TILE_FLAGS)
            out.extend(_u32(value))
        elif key == "unique_id":
            out.append(ATTR_UNIQUE_ID)
            out.extend(_u16_checked("unique_id", value))
    return bytes(out)


def _checked_int(name: str, value: Any, maximum: int) -> int:
    number = int(value)
    if not 0 <= number <= maximum:
        raise ValueError(f"{name} must be between 0 and {maximum}")
    return number


def _u16_checked(name: str, value: Any) -> bytes:
    return struct.pack("<H", _checked_int(name, value, 0xFFFF))
