"""Real-time, read-only inspection of the map region visible in the editor."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from core.editor.item_type_flags import RMEItemTypeCatalog


@dataclass(frozen=True)
class ViewportObservation:
    issue_id: str
    code: str
    severity: str
    category: str
    x: int
    y: int
    z: int
    message: str
    evidence: str
    repair_kind: str = "NONE"
    auto_repairable: bool = False
    prompt_hint: str = ""
    repair: Mapping[str, Any] | None = None


class ViewportObserver:
    """Apply certified ItemType and neighborhood rules without mutating the map."""

    def __init__(self, root: str | Path | None = None) -> None:
        project_root = Path(root).resolve() if root else Path(__file__).resolve().parents[2]
        self.catalog = RMEItemTypeCatalog.load(project_root)

    def analyze(self, snapshot: Mapping[str, Any]) -> dict[str, Any]:
        raw_tiles = list(snapshot.get("tiles", ()))
        tiles = {
            (int(tile["x"]), int(tile["y"]), int(tile["z"])): dict(tile)
            for tile in raw_tiles
            if isinstance(tile, Mapping) and all(key in tile for key in ("x", "y", "z"))
        }
        topology_complete = int(snapshot.get("sample_step", 1) or 1) == 1
        bounds = tuple(int(value) for value in snapshot.get("bounds", ()))
        observations: list[ViewportObservation] = []
        for coord, tile in tiles.items():
            x, y, z = coord
            ground_id = _optional_int(tile.get("ground_id"))
            item_ids = tuple(_item_ids(tile.get("items", ())))
            if ground_id is None and item_ids:
                observations.append(self._issue(
                    "MISSING_GROUND", "error", "material", coord,
                    "Tile con objetos pero sin ground.", f"items={list(item_ids)[:8]}",
                    prompt_hint="Define un GroundBrush certificado para esta zona antes de decorarla.",
                ))
            if ground_id is not None:
                ground = self.catalog.get(ground_id)
                if ground.flag_source == "unknown":
                    observations.append(self._issue(
                        "UNKNOWN_GROUND", "error", "material", coord,
                        "El ground no existe en el catalogo ItemType certificado.", f"ground={ground_id}",
                        prompt_hint="Selecciona un GroundBrush del catalogo RME instalado.",
                    ))
                elif not ground.is_ground:
                    observations.append(self._issue(
                        "NON_GROUND_AS_GROUND", "error", "material", coord,
                        "Un item que no es ground ocupa la capa de piso.", f"ground={ground_id}",
                        prompt_hint="Sustituye el material por un GroundBrush real del bioma.",
                    ))
            unknown = [item_id for item_id in item_ids if self.catalog.get(item_id).flag_source == "unknown"]
            if unknown:
                observations.append(self._issue(
                    "UNKNOWN_ITEM", "error", "asset", coord,
                    "El stack contiene items sin ItemType certificado.", f"items={unknown[:8]}",
                    prompt_hint="Usa solamente materiales y doodads presentes en las paletas RME.",
                ))
            ordered = tuple(self.catalog.sort_items(item_ids))
            if item_ids != ordered:
                observations.append(self._issue(
                    "DRAW_ORDER_MISMATCH", "error", "stack", coord,
                    "El orden del stack no coincide con Tile::addItem de Canary/RME.",
                    f"actual={list(item_ids)} expected={list(ordered)}",
                    repair_kind="REORDER_STACK", auto_repairable=True,
                    repair={"items": ordered},
                ))
            duplicates = sorted({item_id for item_id in item_ids if item_ids.count(item_id) > 1})
            structural_duplicates = [
                item_id for item_id in duplicates
                if any((self.catalog.get(item_id).is_border, self.catalog.get(item_id).is_wall))
            ]
            if structural_duplicates:
                observations.append(self._issue(
                    "DUPLICATE_STACK_ITEM", "warning", "stack", coord,
                    f"El stack estructural repite items en x={x}, y={y}, z={z}.",
                    f"items={structural_duplicates[:8]}",
                    prompt_hint="Reaplica el WallBrush o AutoBorder para reconstruir un unico segmento por orientacion.",
                ))
            walls = [item_id for item_id in item_ids if self.catalog.get(item_id).is_wall]
            if walls and topology_complete and _inside_bounds(coord, bounds) and not self._has_role_neighbor(tiles, coord, "is_wall"):
                observations.append(self._issue(
                    "ISOLATED_WALL", "warning", "architecture", coord,
                    "Fragmento de pared sin continuidad cardinal.", f"walls={walls[:4]}",
                    repair_kind="REBUILD_WALL_NEIGHBORS",
                    prompt_hint="Revisa la huella del edificio, aperturas y orientacion del WallBrush.",
                ))
            borders = [item_id for item_id in item_ids if self.catalog.get(item_id).is_border]
            if borders and topology_complete and _inside_bounds(coord, bounds) and not self._has_ground_transition(tiles, coord):
                observations.append(self._issue(
                    "ORPHAN_BORDER", "warning", "terrain", coord,
                    "Border sin transicion de ground observable en sus vecinos.", f"borders={borders[:4]}",
                    repair_kind="REBUILD_AUTOBORDER",
                    prompt_hint="Reaplica el GroundBrush con AutoBorder en el limite del bioma.",
                ))
        payload = [asdict(item) for item in observations]
        snapshot_hash = _stable_hash({"tiles": raw_tiles, "floor": snapshot.get("floor")})
        return {
            "status": "PASS" if not any(item.severity == "error" for item in observations) else "ISSUES",
            "snapshot_hash": snapshot_hash,
            "floor": snapshot.get("floor"),
            "bounds": list(snapshot.get("bounds", ())),
            "tile_count": len(tiles),
            "observations": payload,
            "counts": {
                severity: sum(item.severity == severity for item in observations)
                for severity in ("error", "warning", "info")
            },
            "safe_repairs": [item.issue_id for item in observations if item.auto_repairable],
            "mutation_performed": False,
        }

    def _has_role_neighbor(
        self, tiles: Mapping[tuple[int, int, int], Mapping[str, Any]], coord: tuple[int, int, int], role: str
    ) -> bool:
        x, y, z = coord
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            neighbor = tiles.get((x + dx, y + dy, z), {})
            if any(getattr(self.catalog.get(item_id), role) for item_id in _item_ids(neighbor.get("items", ()))):
                return True
        return False

    @staticmethod
    def _has_ground_transition(
        tiles: Mapping[tuple[int, int, int], Mapping[str, Any]], coord: tuple[int, int, int]
    ) -> bool:
        x, y, z = coord
        current = _optional_int(tiles.get(coord, {}).get("ground_id"))
        neighbors = {
            _optional_int(tiles.get((x + dx, y + dy, z), {}).get("ground_id"))
            for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0))
        }
        neighbors.discard(None)
        return bool(neighbors and (len(neighbors) > 1 or current not in neighbors))

    @staticmethod
    def _issue(
        code: str, severity: str, category: str, coord: tuple[int, int, int], message: str, evidence: str,
        *, repair_kind: str = "NONE", auto_repairable: bool = False, prompt_hint: str = "",
        repair: Mapping[str, Any] | None = None,
    ) -> ViewportObservation:
        x, y, z = coord
        issue_id = hashlib.sha256(f"{code}:{x}:{y}:{z}:{evidence}".encode("utf-8")).hexdigest()[:16]
        return ViewportObservation(
            issue_id, code, severity, category, x, y, z, message, evidence,
            repair_kind, auto_repairable, prompt_hint, repair,
        )


def _item_ids(values: Iterable[Any]) -> Iterable[int]:
    for value in values or ():
        if isinstance(value, int):
            yield value
        elif isinstance(value, Mapping):
            candidate = value.get("item_id", value.get("id"))
            if candidate is not None:
                try:
                    yield int(candidate)
                except (TypeError, ValueError):
                    continue
        else:
            candidate = getattr(value, "item_id", getattr(value, "id", None))
            if candidate is not None:
                try:
                    yield int(candidate)
                except (TypeError, ValueError):
                    continue


def _optional_int(value: Any) -> int | None:
    try:
        return None if value is None else int(value)
    except (TypeError, ValueError):
        return None


def _stable_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _inside_bounds(coord: tuple[int, int, int], bounds: tuple[int, ...]) -> bool:
    if len(bounds) != 4:
        return True
    x, y, _z = coord
    min_x, min_y, max_x, max_y = bounds
    return min_x < x < max_x - 1 and min_y < y < max_y - 1


__all__ = ["ViewportObservation", "ViewportObserver"]
