from __future__ import annotations

import os
import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from core.otbm.lossless_document import LosslessOTBMDocument, _Patch, _escape_node_payload
from core.otbm.otbm_importer import OTBMAttributeReader, OTBMNode, OTBMNodeReader
from core.world_generator.otbm_world.attributes import encode_supported_attributes


@dataclass(frozen=True)
class TileStackPatch:
    x: int
    y: int
    z: int
    ground_id: int | None
    items: tuple[Any, ...] = ()
    flags: int = 0
    house_id: int | None = None

    @property
    def key(self) -> tuple[int, int, int]:
        return self.x, self.y, self.z


@dataclass(frozen=True)
class TransactionWriteReport:
    destination: str
    patch_count: int
    replaced_tiles: int
    inserted_tiles: int
    validated_tiles: int
    output_size: int
    audit_status: str


@dataclass
class _TileRecord:
    node: OTBMNode
    base_x: int
    base_y: int
    z: int
    end: int
    direct_items: list[tuple[int, bytes, tuple[int, ...]]]


@dataclass(frozen=True)
class _AreaRecord:
    node: OTBMNode
    base_x: int
    base_y: int
    z: int
    end: int


class LosslessOTBMTransactionWriter:
    """Patch edited TILE nodes while retaining every untouched source byte."""

    def __init__(self, source: str | Path) -> None:
        self.source = Path(source)
        if not self.source.is_file():
            raise FileNotFoundError(self.source)

    def write(self, destination: str | Path, patches: Iterable[TileStackPatch]) -> TransactionWriteReport:
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        ordered = tuple(dict((patch.key, patch) for patch in patches).values())
        if not ordered:
            raise ValueError("OTBM transaction has no tile patches")
        document = LosslessOTBMDocument(self.source)
        tiles, areas, map_end = self._index_source(set(patch.key for patch in ordered))
        insertions: dict[tuple[int, int, int], list[TileStackPatch]] = {}
        replaced = 0
        for patch in ordered:
            record = tiles.get(patch.key)
            if record is None:
                if patch.ground_id is None and not patch.items:
                    continue
                area = self._area_for_patch(areas, patch)
                area_key = (area.base_x, area.base_y, area.z) if area else (
                    patch.x & 0xFF00,
                    patch.y & 0xFF00,
                    patch.z,
                )
                insertions.setdefault(area_key, []).append(patch)
                continue
            replacement = (
                b"" if patch.ground_id is None and not patch.items else self._encode_existing_tile(record, patch)
            )
            document._queue_patch(_Patch(record.node.offset, record.end, replacement, f"TILE:{patch.key}"))
            replaced += 1

        inserted = 0
        area_by_key = {(area.base_x, area.base_y, area.z): area for area in areas}
        for area_key, area_patches in insertions.items():
            base_x, base_y, z = area_key
            tile_bytes = b"".join(self._encode_new_tile(patch, base_x, base_y) for patch in area_patches)
            area = area_by_key.get(area_key)
            if area is not None:
                document._queue_patch(_Patch(area.end - 1, area.end - 1, tile_bytes, f"AREA_INSERT:{area_key}"))
            else:
                area_bytes = self._encode_node(0x04, struct.pack("<HHB", base_x, base_y, z), tile_bytes)
                document._queue_patch(_Patch(map_end - 1, map_end - 1, area_bytes, f"AREA_CREATE:{area_key}"))
            inserted += len(area_patches)

        handle = tempfile.NamedTemporaryFile(
            prefix=f".{target.name}.", suffix=".tmp", dir=target.parent, delete=False
        )
        temp = Path(handle.name)
        handle.close()
        try:
            cow = document.write_copy_on_write(temp)
            if cow.status != "PASS":
                raise ValueError("Copy-on-write size invariant failed")
            audit = LosslessOTBMDocument(temp).audit_full_file()
            if audit.status != "PASS":
                raise ValueError(f"Lossless OTBM audit failed: {audit.diagnostics[:5]}")
            validated = self._validate_tiles(temp, ordered)
            os.replace(temp, target)
        finally:
            if temp.exists():
                temp.unlink()
        return TransactionWriteReport(
            str(target),
            len(ordered),
            replaced,
            inserted,
            validated,
            target.stat().st_size,
            audit.status,
        )

    def _index_source(
        self, targets: set[tuple[int, int, int]]
    ) -> tuple[dict[tuple[int, int, int], _TileRecord], list[_AreaRecord], int]:
        tile_records: dict[tuple[int, int, int], _TileRecord] = {}
        areas: list[_AreaRecord] = []
        area: _AreaRecord | None = None
        current: _TileRecord | None = None
        map_end = 0
        with OTBMNodeReader(self.source) as reader:
            def on_node(node: OTBMNode, _context: dict[str, Any]) -> None:
                nonlocal area, current, map_end
                if node.node_type == 0x02:
                    map_end = reader.skip_node(node.offset)
                elif node.node_type == 0x04:
                    base_x, base_y, z = OTBMAttributeReader.parse_tile_area(node.attrs)
                    area = _AreaRecord(node, base_x, base_y, z, reader.skip_node(node.offset))
                    areas.append(area)
                    current = None
                elif node.node_type in (0x05, 0x0E) and area is not None:
                    tile = OTBMAttributeReader.parse_tile(node.attrs, area.base_x, area.base_y, area.z)
                    key = (tile["x"], tile["y"], tile["z"])
                    current = _TileRecord(
                        node, area.base_x, area.base_y, area.z, reader.skip_node(node.offset), []
                    ) if key in targets else None
                    if current is not None:
                        tile_records[key] = current
                elif node.node_type == 0x06 and current is not None and node.depth == current.node.depth + 1:
                    item_id = OTBMAttributeReader.parse_item(node.attrs)["id"]
                    raw = bytes(reader._data[node.offset : reader.skip_node(node.offset)])
                    current.direct_items.append((item_id, raw, self._item_ids_in_raw_node(raw)))

            reader.traverse(on_node, max_nodes=None, max_bytes=None)
        if map_end <= 0:
            raise ValueError("MAP_DATA node not found in source OTBM")
        return tile_records, areas, map_end

    @staticmethod
    def _area_for_patch(areas: list[_AreaRecord], patch: TileStackPatch) -> _AreaRecord | None:
        return next(
            (
                area
                for area in areas
                if area.z == patch.z
                and area.base_x <= patch.x <= area.base_x + 255
                and area.base_y <= patch.y <= area.base_y + 255
            ),
            None,
        )

    def _encode_existing_tile(self, record: _TileRecord, patch: TileStackPatch) -> bytes:
        raw_items = list(record.direct_items)
        children = bytearray()
        if patch.ground_id is not None:
            if raw_items and raw_items[0][0] == patch.ground_id:
                children.extend(raw_items.pop(0)[1])
            else:
                children.extend(self._encode_item({"id": patch.ground_id}))
        pools: dict[int, list[tuple[bytes, tuple[int, ...]]]] = {}
        for item_id, raw, subtree_ids in raw_items:
            pools.setdefault(item_id, []).append((raw, subtree_ids))
        item_list = list(patch.items)
        index = 0
        while index < len(item_list):
            item = item_list[index]
            item_id = self._item_id(item)
            reusable = not isinstance(item, dict) or set(item).issubset({"id", "itemid"})
            if reusable and pools.get(item_id):
                raw, subtree_ids = pools[item_id].pop(0)
                children.extend(raw)
                descendants = list(subtree_ids[1:])
                cursor = index + 1
                while descendants and cursor < len(item_list):
                    if self._item_id(item_list[cursor]) != descendants[0]:
                        break
                    descendants.pop(0)
                    cursor += 1
                index = cursor
            else:
                children.extend(self._encode_item(item))
                index += 1
        node_type, attrs = self._updated_tile_header(record, patch)
        return self._encode_node(node_type, attrs, bytes(children))

    @staticmethod
    def _updated_tile_header(record: _TileRecord, patch: TileStackPatch) -> tuple[int, bytes]:
        """Replace RME map flags/house identity while retaining unknown tile attributes."""
        source = record.node.attrs
        source_offset = 6 if record.node.node_type == 0x0E else 2
        unknown_tail = b""
        offset = source_offset
        while offset < len(source):
            attr_start = offset
            attr = source[offset]
            offset += 1
            if attr == 0x03 and offset + 4 <= len(source):
                offset += 4
            elif attr == 0x09 and offset + 2 <= len(source):
                offset += 2
            else:
                unknown_tail = source[attr_start:]
                break

        attrs = bytearray(source[:2])
        if patch.house_id is not None:
            node_type = 0x0E
            attrs.extend(struct.pack("<I", int(patch.house_id)))
        else:
            node_type = 0x05
        if patch.flags:
            attrs.append(0x03)
            attrs.extend(struct.pack("<I", int(patch.flags)))
        attrs.extend(unknown_tail)
        return node_type, bytes(attrs)

    def _encode_new_tile(self, patch: TileStackPatch, base_x: int, base_y: int) -> bytes:
        offset_x = patch.x - base_x
        offset_y = patch.y - base_y
        if not 0 <= offset_x <= 255 or not 0 <= offset_y <= 255:
            raise ValueError(f"Tile {patch.key} is outside area {(base_x, base_y, patch.z)}")
        attrs = bytearray((offset_x, offset_y))
        if patch.house_id is not None:
            node_type = 0x0E
            attrs.extend(struct.pack("<I", int(patch.house_id)))
        else:
            node_type = 0x05
            if patch.flags:
                attrs.append(0x03)
                attrs.extend(struct.pack("<I", int(patch.flags)))
        children = bytearray()
        if patch.ground_id is not None:
            children.extend(self._encode_item({"id": patch.ground_id}))
        for item in patch.items:
            children.extend(self._encode_item(item))
        return self._encode_node(node_type, bytes(attrs), bytes(children))

    def _encode_item(self, item: Any) -> bytes:
        item_id = self._item_id(item)
        attributes: dict[str, Any] = {}
        children: Iterable[Any] = ()
        if isinstance(item, dict):
            attributes = {
                key: item.get(key)
                for key in (
                    "action_id", "unique_id", "text", "description", "teleport_destination",
                    "depot_id", "house_door_id", "count", "charges",
                )
                if item.get(key) is not None
            }
            children = item.get("children", ()) or ()
        child_bytes = b"".join(self._encode_item(child) for child in children)
        return self._encode_node(
            0x06,
            struct.pack("<H", item_id) + encode_supported_attributes(attributes),
            child_bytes,
        )

    @staticmethod
    def _item_id(item: Any) -> int:
        if isinstance(item, dict):
            value = item.get("id", item.get("itemid"))
        else:
            value = getattr(item, "id", getattr(item, "itemid", item))
        item_id = int(value)
        if not 0 < item_id <= 0xFFFF:
            raise ValueError(f"Invalid OTBM item id: {item_id}")
        return item_id

    @staticmethod
    def _encode_node(node_type: int, attrs: bytes, children: bytes = b"") -> bytes:
        return b"\xFE" + _escape_node_payload(bytes((node_type,)) + attrs) + children + b"\xFF"

    @staticmethod
    def _item_ids_in_raw_node(raw: bytes) -> tuple[int, ...]:
        ids: list[int] = []
        with OTBMNodeReader(b"\x00\x00\x00\x00" + raw) as reader:
            def on_node(node: OTBMNode, _context: dict[str, Any]) -> None:
                if node.node_type == 0x06:
                    ids.append(int(OTBMAttributeReader.parse_item(node.attrs)["id"]))

            reader.traverse(on_node, max_nodes=None, max_bytes=None)
        return tuple(ids)

    @staticmethod
    def _validate_tiles(path: Path, patches: tuple[TileStackPatch, ...]) -> int:
        expected = {patch.key: patch for patch in patches}
        observed: dict[tuple[int, int, int], dict[str, Any]] = {}
        area: tuple[int, int, int] | None = None
        current_key: tuple[int, int, int] | None = None
        current_depth = -1

        with OTBMNodeReader(path) as reader:
            def on_node(node: OTBMNode, _context: dict[str, Any]) -> None:
                nonlocal area, current_key, current_depth
                if node.node_type == 0x04:
                    area = OTBMAttributeReader.parse_tile_area(node.attrs)
                    current_key = None
                    current_depth = -1
                    return
                if node.node_type in (0x05, 0x0E) and area is not None:
                    base_x, base_y, z = area
                    tile = OTBMAttributeReader.parse_tile(
                        node.attrs,
                        base_x,
                        base_y,
                        z,
                        house=node.node_type == 0x0E,
                    )
                    key = (int(tile["x"]), int(tile["y"]), int(tile["z"]))
                    current_key = key if key in expected else None
                    current_depth = node.depth
                    if current_key is not None:
                        observed[current_key] = {
                            "flags": int(tile.get("flags", 0)),
                            "house_id": tile.get("house_id"),
                            "item_ids": ([int(tile["ground"])] if tile.get("ground") else []),
                        }
                    return
                if (
                    node.node_type == 0x06
                    and current_key is not None
                    and node.depth > current_depth
                ):
                    observed[current_key]["item_ids"].append(
                        int(OTBMAttributeReader.parse_item(node.attrs)["id"])
                    )

            reader.traverse(on_node, max_nodes=None, max_bytes=None)

        validated = 0
        for patch in patches:
            tile = observed.get(patch.key)
            if patch.ground_id is None and not patch.items:
                if tile is not None:
                    raise ValueError(f"Deleted tile still present after roundtrip: {patch.key}")
                validated += 1
                continue
            if tile is None:
                raise ValueError(f"Patched tile missing after roundtrip: {patch.key}")
            if int(tile.get("flags", 0)) != int(patch.flags):
                raise ValueError(f"Tile flags mismatch after roundtrip at {patch.key}")
            if tile.get("house_id") != patch.house_id:
                raise ValueError(f"House ID mismatch after roundtrip at {patch.key}")
            actual_ids = list(tile["item_ids"])
            expected_ids = (
                ([int(patch.ground_id)] if patch.ground_id is not None else [])
                + LosslessOTBMTransactionWriter._flatten_item_ids(patch.items)
            )
            if actual_ids != expected_ids:
                raise ValueError(
                    f"Ground/item stack mismatch after roundtrip at {patch.key}: "
                    f"{actual_ids} != {expected_ids}"
                )
            validated += 1
        return validated

    @staticmethod
    def _flatten_item_ids(items: Iterable[Any]) -> list[int]:
        flattened: list[int] = []
        for item in items:
            flattened.append(LosslessOTBMTransactionWriter._item_id(item))
            if isinstance(item, dict):
                flattened.extend(
                    LosslessOTBMTransactionWriter._flatten_item_ids(item.get("children", ()) or ())
                )
        return flattened
