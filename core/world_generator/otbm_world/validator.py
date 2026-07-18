from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .fingerprint import sha256_fingerprint
from .model import OtbmItem, OtbmWorldModel
from .roundtrip import read_otbm_summary
from .serializer import serialize_world


@dataclass(frozen=True)
class OtbmValidationReport:
    valid: bool
    errors: tuple[str, ...]
    metrics: Dict[str, float]
    fingerprint: str

    def to_json_dict(self) -> Dict[str, object]:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "metrics": self.metrics,
            "fingerprint": self.fingerprint,
        }


def validate_serialized_world(world: OtbmWorldModel, data: bytes) -> OtbmValidationReport:
    errors: List[str] = []
    if not data:
        errors.append("binary OTBM is empty")
    deterministic_bytes, _ = serialize_world(world)
    if deterministic_bytes != data:
        errors.append("serializer is not deterministic")
    summary = read_otbm_summary(data)
    errors.extend(summary.errors)
    if summary.tile_count != len(world.tiles):
        errors.append(f"tile count mismatch: {summary.tile_count} != {len(world.tiles)}")
    def count_item_tree(item: OtbmItem) -> int:
        return 1 + sum(count_item_tree(child) for child in item.children)

    item_count = sum(count_item_tree(item) for tile in world.tiles for item in tile.items)
    if summary.item_count != item_count:
        errors.append(f"item count mismatch: {summary.item_count} != {item_count}")
    for tile in world.tiles:
        if not (0 <= tile.x <= 0xFFFF and 0 <= tile.y <= 0xFFFF and 0 <= tile.z <= 0xFF):
            errors.append(f"coordinate out of range: {tile.x},{tile.y},{tile.z}")
        for item in _walk_items(tile.items):
            if not (1 <= item.item_id <= 0xFFFF):
                errors.append(f"invalid item id: {item.item_id}")
        if tile.house_id is not None and not (1 <= int(tile.house_id) <= 0xFFFFFFFF):
            errors.append(f"invalid house id: {tile.house_id}")

    deterministic = 1.0 if deterministic_bytes == data else 0.0
    binary = 1.0 if data and summary.valid else 0.0
    tile_coverage = summary.tile_count / max(1, len(world.tiles))
    roundtrip = 1.0 if summary.valid and not summary.errors else 0.0
    node_consistency = 1.0 if summary.node_ordering_valid else 0.0
    metrics = {
        "OWQI": round((binary + tile_coverage + roundtrip + deterministic) / 4, 6),
        "BCI4": binary,
        "NCI": node_consistency,
        "TCI5": round(min(1.0, tile_coverage), 6),
        "RCI4": roundtrip,
        "DFI": deterministic,
    }
    return OtbmValidationReport(
        valid=not errors and all(value >= 1.0 for value in metrics.values()),
        errors=tuple(errors),
        metrics=metrics,
        fingerprint=sha256_fingerprint(data),
    )


def _walk_items(items: tuple[OtbmItem, ...]):
    for item in items:
        yield item
        yield from _walk_items(item.children)
