from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SpritePhaseTiming:
    duration_min: int = 0
    duration_max: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "duration_min": self.duration_min,
            "duration_max": self.duration_max,
        }


@dataclass(frozen=True)
class SpriteAnimationInfo:
    default_start_phase: int = 0
    synchronized: bool = False
    random_start_phase: bool = False
    loop_type: int = 0
    loop_count: int = 0
    phases: tuple[SpritePhaseTiming, ...] = ()

    @property
    def frame_count(self) -> int:
        return max(1, len(self.phases))

    def to_dict(self) -> dict[str, Any]:
        return {
            "default_start_phase": self.default_start_phase,
            "synchronized": self.synchronized,
            "random_start_phase": self.random_start_phase,
            "loop_type": self.loop_type,
            "loop_count": self.loop_count,
            "phases": [phase.to_dict() for phase in self.phases],
        }


@dataclass(frozen=True)
class AppearanceDatSpriteInfo:
    appearance_id: int
    pattern_width: int = 1
    pattern_height: int = 1
    pattern_depth: int = 1
    layers: int = 1
    sprite_ids: tuple[int, ...] = ()
    animation: SpriteAnimationInfo = field(default_factory=SpriteAnimationInfo)
    frame_group_id: int = 0
    source_offset: int = 0
    message_size: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "appearance_id": self.appearance_id,
            "pattern_width": self.pattern_width,
            "pattern_height": self.pattern_height,
            "pattern_depth": self.pattern_depth,
            "layers": self.layers,
            "sprite_ids": list(self.sprite_ids),
            "animation": self.animation.to_dict(),
            "frame_group_id": self.frame_group_id,
            "source_offset": self.source_offset,
            "message_size": self.message_size,
        }


@dataclass(frozen=True)
class AppearanceDatFlags:
    appearance_id: int
    flags: dict[str, Any] = field(default_factory=dict)
    exact_fields: tuple[str, ...] = ()
    source_offset: int = 0
    message_size: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "appearance_id": self.appearance_id,
            "flags": dict(self.flags),
            "exact_fields": list(self.exact_fields),
            "source_offset": self.source_offset,
            "message_size": self.message_size,
        }


class ProtobufWireReader:
    """Small proto2 wire decoder for Canary appearances.dat Appearance messages."""

    def parse_message(self, payload: bytes) -> dict[int, list[Any]]:
        fields: dict[int, list[Any]] = {}
        pos = 0
        size = len(payload)
        while pos < size:
            key, pos = self._read_varint(payload, pos)
            field_no = key >> 3
            wire_type = key & 0x07
            if field_no <= 0:
                break
            value: Any
            if wire_type == 0:
                value, pos = self._read_varint(payload, pos)
            elif wire_type == 1:
                value = payload[pos : pos + 8]
                pos += 8
            elif wire_type == 2:
                length, pos = self._read_varint(payload, pos)
                value = payload[pos : pos + length]
                pos += length
            elif wire_type == 5:
                value = payload[pos : pos + 4]
                pos += 4
            else:
                break
            fields.setdefault(field_no, []).append(value)
        return fields

    def first_varint(self, fields: dict[int, list[Any]], number: int, default: int = 0) -> int:
        values = fields.get(number) or []
        value = values[0] if values else default
        return int(value) if isinstance(value, int) else default

    def nested(self, value: Any) -> dict[int, list[Any]]:
        if isinstance(value, bytes):
            return self.parse_message(value)
        return {}

    def _read_varint(self, payload: bytes, pos: int) -> tuple[int, int]:
        shift = 0
        result = 0
        while pos < len(payload):
            byte = payload[pos]
            pos += 1
            result |= (byte & 0x7F) << shift
            if not byte & 0x80:
                return result, pos
            shift += 7
        return result, pos


class AppearanceDatFlagExtractor:
    """Extracts exact ItemType/render flags from official appearances.dat.

    The field numbers are taken from Canary's source/protobuf/appearances.proto.
    """

    BOOLEAN_FLAGS = {
        2: "clip",
        3: "bottom",
        4: "top",
        5: "container",
        6: "cumulative",
        7: "usable",
        8: "forceuse",
        9: "multiuse",
        12: "liquidpool",
        13: "unpass",
        14: "unmove",
        15: "unsight",
        16: "avoid",
        17: "no_movement_animation",
        18: "take",
        19: "liquidcontainer",
        20: "hang",
        22: "rotate",
        24: "dont_hide",
        25: "translucent",
        28: "lying_object",
        29: "animate_always",
        32: "fullbank",
        33: "ignore_look",
        37: "wrap",
        38: "unwrap",
        39: "topeffect",
        42: "corpse",
        43: "player_corpse",
        45: "ammo",
        46: "show_off_socket",
        47: "reportable",
    }
    NESTED_FLAGS = {
        1: "bank",
        10: "write",
        11: "write_once",
        21: "hook",
        23: "light",
        26: "shift",
        27: "height",
        30: "automap",
        31: "lenshelp",
        34: "clothes",
        35: "default_action",
        36: "market",
        40: "npcsaledata",
        41: "changedtoexpire",
        44: "cyclopediaitem",
        48: "upgradeclassification",
    }

    def __init__(self, appearances_path: str | Path) -> None:
        self.appearances_path = Path(appearances_path)
        self.reader = ProtobufWireReader()
        self._data: bytes | None = None

    def extract_from_catalog_entry(self, appearance_id: int, entry: dict[str, Any]) -> AppearanceDatFlags:
        offset = int(entry.get("offset", 0) or 0)
        message_size = int(entry.get("message_size", 0) or 0)
        if message_size <= 0:
            return AppearanceDatFlags(int(appearance_id))
        payload = self._bytes()[offset : offset + message_size]
        message = self.reader.parse_message(payload)
        if set(message) == {1} and message.get(1) and isinstance(message[1][0], bytes):
            message = self.reader.nested(message[1][0])
        flags_payload = (message.get(3) or [b""])[0]
        flags_message = self.reader.nested(flags_payload)
        exact = self._extract_flags(flags_message)
        return AppearanceDatFlags(
            appearance_id=int(appearance_id),
            flags=exact,
            exact_fields=tuple(sorted(exact)),
            source_offset=offset,
            message_size=message_size,
        )

    def extract_sprite_info_from_catalog_entry(
        self,
        appearance_id: int,
        entry: dict[str, Any],
        frame_group_index: int = 0,
    ) -> AppearanceDatSpriteInfo:
        """Read SpriteInfo and SpriteAnimation using appearances.proto fields."""
        offset = int(entry.get("offset", 0) or 0)
        message_size = int(entry.get("message_size", 0) or 0)
        if message_size <= 0:
            return AppearanceDatSpriteInfo(int(appearance_id))
        message = self._appearance_message(offset, message_size)
        groups = message.get(2) or []
        if not groups:
            return AppearanceDatSpriteInfo(
                int(appearance_id), source_offset=offset, message_size=message_size
            )
        group = self.reader.nested(groups[min(max(0, frame_group_index), len(groups) - 1)])
        sprite_payload = (group.get(3) or [b""])[0]
        sprite = self.reader.nested(sprite_payload)
        animation = self._extract_animation(sprite)
        sprite_ids = tuple(int(value) for value in sprite.get(5, []) if isinstance(value, int))
        base_count = (
            max(1, self.reader.first_varint(sprite, 1, 1))
            * max(1, self.reader.first_varint(sprite, 2, 1))
            * max(1, self.reader.first_varint(sprite, 3, 1))
            * max(1, self.reader.first_varint(sprite, 4, 1))
        )
        if not animation.phases and len(sprite_ids) > base_count:
            inferred_frames = max(1, len(sprite_ids) // base_count)
            animation = SpriteAnimationInfo(
                phases=tuple(SpritePhaseTiming() for _ in range(inferred_frames))
            )
        return AppearanceDatSpriteInfo(
            appearance_id=int(appearance_id),
            pattern_width=max(1, self.reader.first_varint(sprite, 1, 1)),
            pattern_height=max(1, self.reader.first_varint(sprite, 2, 1)),
            pattern_depth=max(1, self.reader.first_varint(sprite, 3, 1)),
            layers=max(1, self.reader.first_varint(sprite, 4, 1)),
            sprite_ids=sprite_ids,
            animation=animation,
            frame_group_id=self.reader.first_varint(group, 2),
            source_offset=offset,
            message_size=message_size,
        )

    def audit(self) -> dict[str, Any]:
        return {
            "appearance_dat_flag_extractor_ready": self.appearances_path.exists(),
            "source": str(self.appearances_path),
            "schema_source": "projects/canary-extracted/canary-map-editor-v4.0-windows/source/protobuf/appearances.proto",
            "exact_flags": [
                "unpass",
                "unmove",
                "unsight",
                "avoid",
                "no_movement_animation",
                "take",
                "automap.color",
                "height.elevation",
                "shift.x",
                "shift.y",
                "light.brightness",
                "light.color",
            ],
            "exact_sprite_fields": [
                "pattern_width",
                "pattern_height",
                "pattern_depth",
                "layers",
                "sprite_ids",
                "animation.default_start_phase",
                "animation.synchronized",
                "animation.random_start_phase",
                "animation.loop_type",
                "animation.loop_count",
                "animation.sprite_phase.duration_min",
                "animation.sprite_phase.duration_max",
            ],
        }

    def _appearance_message(self, offset: int, message_size: int) -> dict[int, list[Any]]:
        payload = self._bytes()[offset : offset + message_size]
        message = self.reader.parse_message(payload)
        if set(message) == {1} and message.get(1) and isinstance(message[1][0], bytes):
            return self.reader.nested(message[1][0])
        return message

    def _extract_animation(self, sprite: dict[int, list[Any]]) -> SpriteAnimationInfo:
        payload = (sprite.get(6) or [b""])[0]
        animation = self.reader.nested(payload)
        phases = []
        for phase_payload in animation.get(6, []):
            phase = self.reader.nested(phase_payload)
            phases.append(
                SpritePhaseTiming(
                    duration_min=self.reader.first_varint(phase, 1),
                    duration_max=self.reader.first_varint(phase, 2),
                )
            )
        loop_type = self.reader.first_varint(animation, 4)
        if loop_type >= (1 << 63):
            loop_type -= 1 << 64
        return SpriteAnimationInfo(
            default_start_phase=self.reader.first_varint(animation, 1),
            synchronized=bool(self.reader.first_varint(animation, 2)),
            random_start_phase=bool(self.reader.first_varint(animation, 3)),
            loop_type=loop_type,
            loop_count=self.reader.first_varint(animation, 5),
            phases=tuple(phases),
        )

    def _extract_flags(self, flags_message: dict[int, list[Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for number, name in self.BOOLEAN_FLAGS.items():
            if number in flags_message:
                result[name] = bool(self.reader.first_varint(flags_message, number))
        if 23 in flags_message:
            light = self.reader.nested(flags_message[23][0])
            result["light_level"] = self.reader.first_varint(light, 1)
            result["light_color"] = self.reader.first_varint(light, 2)
        if 26 in flags_message:
            shift = self.reader.nested(flags_message[26][0])
            result["draw_offset_x"] = self.reader.first_varint(shift, 1)
            result["draw_offset_y"] = self.reader.first_varint(shift, 2)
        if 27 in flags_message:
            height = self.reader.nested(flags_message[27][0])
            result["elevation"] = self.reader.first_varint(height, 1)
        if 30 in flags_message:
            automap = self.reader.nested(flags_message[30][0])
            result["automap_color"] = self.reader.first_varint(automap, 1)
        if 21 in flags_message:
            hook = self.reader.nested(flags_message[21][0])
            result["hook_direction"] = self.reader.first_varint(hook, 1)
        if 1 in flags_message:
            bank = self.reader.nested(flags_message[1][0])
            result["waypoints"] = self.reader.first_varint(bank, 1)
        return result

    def _bytes(self) -> bytes:
        if self._data is None:
            self._data = self.appearances_path.read_bytes()
        return self._data
