from __future__ import annotations

import hashlib
import shutil
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core.otbm.otbm_importer import OTBMAttributeReader, OTBMNode, OTBMNodeReader, RME_NODE_NAMES
from core.world_generator.otbm_world.attributes import encode_supported_attributes


KNOWN_ITEM_ATTRIBUTES = {
    0x04: ("action_id", 2),
    0x05: ("unique_id", 2),
    0x06: ("text", "string"),
    0x07: ("description", "string"),
    0x08: ("teleport_destination", 5),
    0x0A: ("depot_id", 2),
    0x0C: ("rune_charges", 1),
    0x0E: ("house_door_id", 1),
    0x0F: ("count", 1),
    0x10: ("duration", 4),
    0x11: ("decaying_state", 1),
    0x12: ("written_date", 4),
    0x13: ("written_by", "string"),
    0x14: ("sleeper_guid", 4),
    0x15: ("sleep_start", 4),
    0x16: ("charges", 2),
    0x80: ("attribute_map", "opaque_tail"),
}


@dataclass(frozen=True)
class LosslessOTBMAudit:
    source: str
    source_sha256: str
    file_size: int
    full_file_scanned: bool
    truncated: bool
    nodes_scanned: int
    node_counts: dict[str, int]
    unknown_node_counts: dict[str, int]
    item_attribute_counts: dict[str, int]
    unknown_item_attribute_counts: dict[str, int]
    floors: tuple[int, ...]
    diagnostics: tuple[str, ...]

    @property
    def status(self) -> str:
        return "PASS" if self.full_file_scanned and not self.truncated and not self.diagnostics else "BLOCKED"

    def to_dict(self) -> dict[str, Any]:
        return {"stage": "Lossless OTBM Full-file Audit", "status": self.status, **asdict(self)}


@dataclass(frozen=True)
class ByteIdentityReport:
    status: str
    source_sha256: str
    output_sha256: str
    source_size: int
    output_size: int
    byte_identical: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CopyOnWriteReport:
    status: str
    source_sha256: str
    output_sha256: str
    source_size: int
    output_size: int
    patch_count: int
    source_bytes_replaced: int
    output_bytes_inserted: int
    untouched_source_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class _Patch:
    start: int
    end: int
    replacement: bytes
    label: str


class LosslessOTBMDocument:
    """Read-only indexed source plus copy-on-write foundation for lossless OTBM edits."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if not self.path.is_file():
            raise FileNotFoundError(self.path)
        self._patches: list[_Patch] = []

    def audit_full_file(self) -> LosslessOTBMAudit:
        source_hash = _sha256(self.path)
        item_attributes: Counter[str] = Counter()
        unknown_item_attributes: Counter[str] = Counter()
        unknown_nodes: Counter[str] = Counter()
        diagnostics: list[str] = []

        def on_node(node: OTBMNode, _context: dict[str, Any]) -> None:
            if node.node_type not in RME_NODE_NAMES:
                unknown_nodes[f"0x{node.node_type:02X}"] += 1
            if node.node_type == 0x06:
                known, unknown, errors = _scan_item_attributes(node.attrs[2:])
                item_attributes.update(known)
                unknown_item_attributes.update(unknown)
                if errors and len(diagnostics) < 100:
                    diagnostics.extend(f"item@{node.offset}: {error}" for error in errors)

        with OTBMNodeReader(self.path) as reader:
            stats = reader.traverse(on_node, max_nodes=None, max_bytes=None)
            full_file_scanned = not stats.truncated
            file_size = reader.file_size
        return LosslessOTBMAudit(
            source=str(self.path),
            source_sha256=source_hash,
            file_size=file_size,
            full_file_scanned=full_file_scanned,
            truncated=stats.truncated,
            nodes_scanned=stats.nodes_visited,
            node_counts=dict(sorted(stats.node_counts.items())),
            unknown_node_counts=dict(sorted(unknown_nodes.items())),
            item_attribute_counts=dict(sorted(item_attributes.items())),
            unknown_item_attribute_counts=dict(sorted(unknown_item_attributes.items())),
            floors=tuple(sorted(stats.floors_detected)),
            diagnostics=tuple(diagnostics),
        )

    def write_unchanged(self, output: str | Path) -> ByteIdentityReport:
        target = Path(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.resolve() == self.path.resolve():
            raise ValueError("Lossless output must not overwrite its source")
        with self.path.open("rb") as source, target.open("wb") as destination:
            shutil.copyfileobj(source, destination, length=1024 * 1024)
        source_hash = _sha256(self.path)
        output_hash = _sha256(target)
        source_size = self.path.stat().st_size
        output_size = target.stat().st_size
        identical = source_hash == output_hash and source_size == output_size
        return ByteIdentityReport(
            "PASS" if identical else "BLOCKED",
            source_hash,
            output_hash,
            source_size,
            output_size,
            identical,
        )

    def queue_item_attribute(self, node_offset: int, key: str, value: Any) -> None:
        """Patch one known item attribute while retaining every unrelated decoded byte."""
        with OTBMNodeReader(self.path) as reader:
            node = reader.read_node(int(node_offset))
        if node.node_type != 0x06:
            raise ValueError(f"node at {node_offset} is {node.name}, not ITEM")
        if len(node.attrs) < 2:
            raise ValueError("ITEM payload has no item id")
        updated = node.attrs[:2] + _replace_item_attribute(node.attrs[2:], key, value)
        replacement = _escape_node_payload(bytes([node.node_type]) + updated)
        self._queue_patch(
            _Patch(node.offset + 1, node.delimiter_offset, replacement, f"ITEM:{node_offset}:{key}")
        )

    def queue_node_attributes(self, node_offset: int, attributes: bytes) -> None:
        """Low-level replacement for known node schemas; child bytes remain untouched."""
        with OTBMNodeReader(self.path) as reader:
            node = reader.read_node(int(node_offset))
        replacement = _escape_node_payload(bytes([node.node_type]) + bytes(attributes))
        self._queue_patch(_Patch(node.offset + 1, node.delimiter_offset, replacement, f"NODE:{node_offset}"))

    def write_copy_on_write(self, output: str | Path) -> CopyOnWriteReport:
        target = Path(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.resolve() == self.path.resolve():
            raise ValueError("Copy-on-write output must not overwrite its source")
        patches = sorted(self._patches, key=lambda patch: patch.start)
        source_size = self.path.stat().st_size
        cursor = 0
        with self.path.open("rb") as source, target.open("wb") as destination:
            for patch in patches:
                source.seek(cursor)
                _copy_exact(source, destination, patch.start - cursor)
                destination.write(patch.replacement)
                cursor = patch.end
            source.seek(cursor)
            shutil.copyfileobj(source, destination, length=1024 * 1024)
        replaced = sum(patch.end - patch.start for patch in patches)
        inserted = sum(len(patch.replacement) for patch in patches)
        source_hash = _sha256(self.path)
        output_hash = _sha256(target)
        output_size = target.stat().st_size
        return CopyOnWriteReport(
            "PASS" if output_size == source_size - replaced + inserted else "BLOCKED",
            source_hash,
            output_hash,
            source_size,
            output_size,
            len(patches),
            replaced,
            inserted,
            source_size - replaced,
        )

    def queue_canary_draw_order(self, item_catalog: Any) -> int:
        """Reorder direct ITEM children exactly like Canary Tile::addItem."""
        current: dict[str, Any] | None = None
        changed = 0

        with OTBMNodeReader(self.path) as reader:
            def finish_tile() -> None:
                nonlocal current, changed
                if current is None or len(current["items"]) < 2:
                    current = None
                    return
                records = current["items"]
                ground_records = [record for record in records if item_catalog.get(record[0]).is_ground]
                object_records = [record for record in records if not item_catalog.get(record[0]).is_ground]
                ordered_object_ids = item_catalog.sort_items([record[0] for record in object_records])
                pools: dict[int, list[tuple[int, int, int]]] = {}
                for record in object_records:
                    pools.setdefault(record[0], []).append(record)
                ordered_records = (ground_records[-1:] if ground_records else []) + [
                    pools[item_id].pop(0) for item_id in ordered_object_ids
                ]
                if ordered_records == records:
                    current = None
                    return
                start = records[0][1]
                end = records[-1][2]
                replacement = b"".join(bytes(reader._data[a:b]) for _item_id, a, b in ordered_records)
                self._queue_patch(_Patch(start, end, replacement, f"TILE_DRAW_ORDER:{current['offset']}"))
                changed += 1
                current = None

            def on_node(node: OTBMNode, _context: dict[str, Any]) -> None:
                nonlocal current
                if node.node_type in (0x05, 0x0E):
                    finish_tile()
                    current = {"offset": node.offset, "depth": node.depth, "items": []}
                elif node.node_type == 0x06 and current is not None and node.depth == current["depth"] + 1:
                    item_id = OTBMAttributeReader.parse_item(node.attrs)["id"]
                    current["items"].append((item_id, node.offset, reader.skip_node(node.offset)))

            reader.traverse(on_node, max_nodes=None, max_bytes=None)
            finish_tile()
        return changed

    def _queue_patch(self, patch: _Patch) -> None:
        for existing in self._patches:
            if patch.start < existing.end and existing.start < patch.end:
                raise ValueError(f"Copy-on-write patches overlap: {existing.label} and {patch.label}")
        self._patches.append(patch)


def _scan_item_attributes(data: bytes) -> tuple[Counter[str], Counter[str], list[str]]:
    known: Counter[str] = Counter()
    unknown: Counter[str] = Counter()
    errors: list[str] = []
    offset = 0
    while offset < len(data):
        attribute = data[offset]
        offset += 1
        contract = KNOWN_ITEM_ATTRIBUTES.get(attribute)
        if contract is None:
            unknown[f"0x{attribute:02X}"] += 1
            break  # Unknown width: preserve the remaining raw payload, never guess alignment.
        name, width = contract
        known[name] += 1
        if width == "opaque_tail":
            break
        if width == "string":
            if offset + 2 > len(data):
                errors.append(f"truncated {name} length")
                break
            size = OTBMAttributeReader.u16(data, offset)
            offset += 2
            if offset + size > len(data):
                errors.append(f"truncated {name} payload")
                break
            offset += size
            continue
        size = int(width)
        if offset + size > len(data):
            errors.append(f"truncated {name}")
            break
        offset += size
    return known, unknown, errors


def _replace_item_attribute(data: bytes, key: str, value: Any) -> bytes:
    attribute_by_name = {name: attribute for attribute, (name, _width) in KNOWN_ITEM_ATTRIBUTES.items()}
    if key not in attribute_by_name:
        raise ValueError(f"Unsupported copy-on-write item attribute: {key}")
    target_attribute = attribute_by_name[key]
    segments, opaque_tail = _item_attribute_segments(data)
    encoded = b"" if value is None else encode_supported_attributes({key: value})
    output = bytearray()
    replaced = False
    for attribute, segment in segments:
        if attribute == target_attribute:
            if not replaced:
                output.extend(encoded)
                replaced = True
            continue
        output.extend(segment)
    if not replaced:
        output.extend(encoded)
    output.extend(opaque_tail)
    return bytes(output)


def _item_attribute_segments(data: bytes) -> tuple[list[tuple[int, bytes]], bytes]:
    segments: list[tuple[int, bytes]] = []
    offset = 0
    while offset < len(data):
        start = offset
        attribute = data[offset]
        offset += 1
        contract = KNOWN_ITEM_ATTRIBUTES.get(attribute)
        if contract is None:
            return segments, data[start:]
        _name, width = contract
        if width == "opaque_tail":
            return segments, data[start:]
        if width == "string":
            if offset + 2 > len(data):
                return segments, data[start:]
            size = OTBMAttributeReader.u16(data, offset)
            offset += 2 + size
        else:
            offset += int(width)
        if offset > len(data):
            return segments, data[start:]
        segments.append((attribute, data[start:offset]))
    return segments, b""


def _escape_node_payload(payload: bytes) -> bytes:
    output = bytearray()
    for byte in payload:
        if byte in (0xFD, 0xFE, 0xFF):
            output.append(0xFD)
        output.append(byte)
    return bytes(output)


def _copy_exact(source: Any, destination: Any, size: int) -> None:
    remaining = max(0, int(size))
    while remaining:
        chunk = source.read(min(1024 * 1024, remaining))
        if not chunk:
            raise IOError("Unexpected end of OTBM source while applying copy-on-write patches")
        destination.write(chunk)
        remaining -= len(chunk)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
