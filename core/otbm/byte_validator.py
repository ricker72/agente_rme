"""
byte_validator.py — HITO 26.1A

Centralised byte-range validation for the OTBM export pipeline.

The bug we are fixing:
    struct.error: 'B' format requires 0 <= number <= 255
was raised whenever a tile id, item id, house id, action id, zone id,
flag, attribute or coord overflowed its declared integer type.

This module provides:
    * validate_byte(value, context)  -> raises ValueError on bad
    * validate_word(value, context)  -> raises ValueError on bad
    * validate_dword(value, context) -> raises ValueError on bad
    * ByteValidator class with both strict and coerce_* helpers

The same instance is shared by OtbmValidator (post-write byte
validation) and the export pipeline (pre-write value sanitisation).
"""

from __future__ import annotations

from typing import List


def validate_byte(value, context: str = "byte") -> int:
    """
    Validate that ``value`` fits in a single unsigned byte (uint8).

    Returns the value as int. Raises ValueError if the value is
    not in [0, 255]. ``None`` is treated as 0. Non-numeric values
    raise ValueError.
    """
    if value is None:
        return 0
    try:
        iv = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{context}: cannot convert {value!r} to uint8")
    if iv < 0 or iv > 255:
        raise ValueError(f"{context}: value {iv} out of uint8 range [0, 255]")
    return iv


def validate_word(value, context: str = "word") -> int:
    """Validate that ``value`` fits in a 16-bit unsigned int (uint16)."""
    if value is None:
        return 0
    try:
        iv = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{context}: cannot convert {value!r} to uint16")
    if iv < 0 or iv > 65535:
        raise ValueError(f"{context}: value {iv} out of uint16 range [0, 65535]")
    return iv


def validate_dword(value, context: str = "dword") -> int:
    """Validate that ``value`` fits in a 32-bit unsigned int (uint32)."""
    if value is None:
        return 0
    try:
        iv = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{context}: cannot convert {value!r} to uint32")
    if iv < 0 or iv > 0xFFFFFFFF:
        raise ValueError(f"{context}: value {iv} out of uint32 range [0, 4294967295]")
    return iv


class ByteValidator:
    """
    Stateful, structured byte-range validator used by the OTBM pipeline.

    Strict methods raise ValueError on out-of-range. Coerce methods
    clamp to the range and log the change to ``self.warnings``.

    The same instance can be shared by ``OtbmValidator`` (post-write
    byte-level validation) and the export pipeline (pre-write value
    sanitisation).
    """

    MAX_U8 = 255
    MAX_U16 = 65535
    MAX_U32 = 0xFFFFFFFF
    MAX_TILE_ID = 65535
    MAX_ITEM_ID = 65535
    MAX_HOUSE_ID = 0xFFFFFFFF
    MAX_ACTION_ID = 65535
    MAX_UNIQUE_ID = 65535
    MAX_ZONE_ID = 0xFFFFFFFF
    MAX_SPAWN_RADIUS = 255
    MAX_TILE_OFFSET = 255
    MAX_Z = 255

    def __init__(self, strict: bool = False):
        self.strict = strict
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.validated_count = 0

    # ---- Strict validators -----------------------------------------
    def validate_tile_id(self, value, context: str = "tile_id") -> int:
        return validate_word(value, context)

    def validate_item_id(self, value, context: str = "item_id") -> int:
        return validate_word(value, context)

    def validate_house_id(self, value, context: str = "house_id") -> int:
        return validate_dword(value, context)

    def validate_action_id(self, value, context: str = "action_id") -> int:
        return validate_word(value, context)

    def validate_unique_id(self, value, context: str = "unique_id") -> int:
        return validate_word(value, context)

    def validate_zone_id(self, value, context: str = "zone_id") -> int:
        return validate_dword(value, context)

    def validate_flag(self, value, context: str = "flag") -> int:
        return validate_dword(value, context)

    def validate_attribute(self, value, context: str = "attribute") -> int:
        return validate_byte(value, context)

    def validate_tile_offset(self, value, context: str = "tile_offset") -> int:
        return validate_byte(value, context)

    def validate_spawn_radius(self, value, context: str = "spawn_radius") -> int:
        return validate_byte(value, context)

    def validate_z(self, value, context: str = "z") -> int:
        return validate_byte(value, context)

    # ---- Coercing validators (clamp + log) -------------------------
    def coerce_byte(self, value, context: str = "byte") -> int:
        return self._coerce(value, 0, self.MAX_U8, context)

    def coerce_word(self, value, context: str = "word") -> int:
        return self._coerce(value, 0, self.MAX_U16, context)

    def coerce_dword(self, value, context: str = "dword") -> int:
        return self._coerce(value, 0, self.MAX_U32, context)

    def coerce_tile_offset(self, value, context: str = "tile_offset") -> int:
        return self._coerce(value, 0, self.MAX_TILE_OFFSET, context)

    def coerce_spawn_radius(self, value, context: str = "spawn_radius") -> int:
        return self._coerce(value, 0, self.MAX_SPAWN_RADIUS, context)

    def coerce_z(self, value, context: str = "z") -> int:
        return self._coerce(value, 0, self.MAX_Z, context)

    def _coerce(self, value, lo: int, hi: int, context: str) -> int:
        if value is None:
            self.warnings.append(f"{context}: None -> {lo}")
            return lo
        try:
            iv = int(value)
        except (TypeError, ValueError):
            self.warnings.append(f"{context}: {value!r} not numeric -> {lo}")
            return lo
        if iv < lo or iv > hi:
            clamped = max(lo, min(hi, iv))
            msg = f"{context}: {iv} out of [{lo},{hi}] -> {clamped}"
            if self.strict:
                self.errors.append(msg)
                raise ValueError(msg)
            self.warnings.append(msg)
            return clamped
        self.validated_count += 1
        return iv

    # ---- Bulk helpers ----------------------------------------------
    def validate_tile_dict(self, tile: dict) -> List[str]:
        """
        Run the validator over every known numeric field of a tile dict.

        Returns the list of warnings generated (errors if strict).
        Never raises unless strict=True.
        """
        local: List[str] = []
        before_warn = len(self.warnings)

        for key in ("offset_x", "offset_y"):
            if key in tile and tile[key] is not None:
                try:
                    self.coerce_tile_offset(tile[key], context=f"tile.{key}")
                except ValueError as e:
                    local.append(str(e))

        if "z" in tile and tile["z"] is not None:
            try:
                self.coerce_z(tile["z"], context="tile.z")
            except ValueError as e:
                local.append(str(e))

        for i, item in enumerate(tile.get("items", []) or []):
            iid = item.get("id") if isinstance(item, dict) else item
            try:
                self.coerce_word(iid, context=f"tile.item[{i}].id")
            except ValueError as e:
                local.append(str(e))
            if isinstance(item, dict):
                for sub in ("action_id", "unique_id", "subtype", "charges", "count"):
                    if sub in item and item[sub] is not None:
                        try:
                            if sub in ("action_id", "unique_id"):
                                self.coerce_word(item[sub], context=f"tile.item[{i}].{sub}")
                            else:
                                self.coerce_byte(item[sub], context=f"tile.item[{i}].{sub}")
                        except ValueError as e:
                            local.append(str(e))

        if "flags" in tile and tile["flags"] is not None:
            try:
                self.coerce_dword(tile["flags"], context="tile.flags")
            except ValueError as e:
                local.append(str(e))

        return self.warnings[before_warn:]
