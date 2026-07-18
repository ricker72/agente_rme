from __future__ import annotations

import json
import xml.etree.ElementTree as ET
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.world_generator.rme_materials_necro_v5 import resolve_materials_dir


EDGE_DELTAS: dict[str, tuple[int, int]] = {
    "n": (0, -1),
    "e": (1, 0),
    "s": (0, 1),
    "w": (-1, 0),
    "cnw": (-1, -1),
    "cne": (1, -1),
    "csw": (-1, 1),
    "cse": (1, 1),
    "dnw": (-1, -1),
    "dne": (1, -1),
    "dsw": (-1, 1),
    "dse": (1, 1),
}

RME_FULL_WALL_ALIGNMENTS: tuple[str, ...] = (
    "pole",
    "south end",
    "east end",
    "northwest diagonal",
    "west end",
    "northeast diagonal",
    "horizontal",
    "south T",
    "north end",
    "vertical",
    "southwest diagonal",
    "east T",
    "southeast diagonal",
    "west T",
    "north T",
    "intersection",
)

RME_HALF_WALL_ALIGNMENTS: tuple[str, ...] = (
    "pole", "vertical", "horizontal", "northwest diagonal",
    "pole", "vertical", "horizontal", "northwest diagonal",
    "pole", "vertical", "horizontal", "northwest diagonal",
    "pole", "vertical", "horizontal", "northwest diagonal",
)

RME_CONNECTED_OFFSETS: tuple[tuple[str, int, int], ...] = (
    ("nw", -1, -1),
    ("n", 0, -1),
    ("ne", 1, -1),
    ("w", -1, 0),
    ("e", 1, 0),
    ("sw", -1, 1),
    ("s", 0, 1),
    ("se", 1, 1),
)

RME_CONNECTED_SYMBOL_TO_ALIGNMENT: dict[str, str] = {
    "TABLE_ALONE": "alone",
    "TABLE_VERTICAL": "vertical",
    "TABLE_HORIZONTAL": "horizontal",
    "TABLE_NORTH_END": "north",
    "TABLE_SOUTH_END": "south",
    "TABLE_EAST_END": "east",
    "TABLE_WEST_END": "west",
    "CARPET_CENTER": "center",
    "NORTH_HORIZONTAL": "n",
    "EAST_HORIZONTAL": "e",
    "SOUTH_HORIZONTAL": "s",
    "WEST_HORIZONTAL": "w",
    "NORTHWEST_CORNER": "cnw",
    "NORTHEAST_CORNER": "cne",
    "SOUTHEAST_CORNER": "cse",
    "SOUTHWEST_CORNER": "csw",
    "NORTHWEST_DIAGONAL": "dnw",
    "NORTHEAST_DIAGONAL": "dne",
    "SOUTHEAST_DIAGONAL": "dse",
    "SOUTHWEST_DIAGONAL": "dsw",
}


def load_rme_connected_item_tables() -> dict[str, tuple[str, ...]]:
    path = Path(__file__).resolve().parents[2] / "data" / "rme_connected_item_tables.json"
    try:
        payload = json.loads(path.read_text(encoding="ascii"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot load certified RME connected-item tables: {path}") from exc
    tables: dict[str, tuple[str, ...]] = {}
    for kind in ("table", "carpet"):
        source = payload.get(kind)
        if not isinstance(source, dict) or len(source) != 256:
            raise RuntimeError(f"Certified RME {kind} table must contain exactly 256 masks")
        try:
            symbols = tuple(str(source[str(mask)]) for mask in range(256))
        except KeyError as exc:
            raise RuntimeError(f"Certified RME {kind} table is missing mask {exc.args[0]}") from exc
        unknown = set(symbols) - RME_CONNECTED_SYMBOL_TO_ALIGNMENT.keys()
        if unknown:
            raise RuntimeError(f"Certified RME {kind} table has unknown symbols: {sorted(unknown)}")
        tables[kind] = symbols
    return tables


RME_CONNECTED_ITEM_TABLES = load_rme_connected_item_tables()

RME_BORDER_SYMBOL_TO_EDGE: dict[str, str] = {
    "NORTH_HORIZONTAL": "n",
    "EAST_HORIZONTAL": "e",
    "SOUTH_HORIZONTAL": "s",
    "WEST_HORIZONTAL": "w",
    "NORTHWEST_CORNER": "cnw",
    "NORTHEAST_CORNER": "cne",
    "SOUTHEAST_CORNER": "cse",
    "SOUTHWEST_CORNER": "csw",
    "NORTHWEST_DIAGONAL": "dnw",
    "NORTHEAST_DIAGONAL": "dne",
    "SOUTHEAST_DIAGONAL": "dse",
    "SOUTHWEST_DIAGONAL": "dsw",
}


def load_rme_ground_border_table() -> tuple[tuple[str, ...], ...]:
    path = Path(__file__).resolve().parents[2] / "data" / "rme_ground_border_table.json"
    try:
        payload = json.loads(path.read_text(encoding="ascii"))
        source = payload["ground_border"]
        rows = tuple(tuple(source[str(mask)]) for mask in range(256))
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot load certified RME ground-border table: {path}") from exc
    if len(rows) != 256 or any(symbol not in RME_BORDER_SYMBOL_TO_EDGE for row in rows for symbol in row):
        raise RuntimeError("Certified RME ground-border table is incomplete or contains unknown symbols")
    return rows


RME_GROUND_BORDER_TABLE = load_rme_ground_border_table()


def load_rme_ground_specific_cases() -> tuple[dict[str, Any], ...]:
    path = Path(__file__).resolve().parents[2] / "data" / "rme_ground_specific_cases.json"
    try:
        payload = json.loads(path.read_text(encoding="ascii"))
        cases = tuple(payload["cases"])
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot load certified RME ground specific cases: {path}") from exc
    if len(cases) != 117:
        raise RuntimeError(f"Certified RME ground specific cases expected 117 entries, got {len(cases)}")
    return cases


RME_GROUND_SPECIFIC_CASES = load_rme_ground_specific_cases()
RME_GROUND_SPECIFIC_REPLACEMENT_IDS = {
    int(case["action"].get("replacement_item_id", 0))
    for case in RME_GROUND_SPECIFIC_CASES
    if int(case["action"].get("replacement_item_id", 0)) > 0
}


def load_certified_sprite_backed_ids(root: Path) -> tuple[set[int], str]:
    """Load the compact catalog derived from appearances.dat and the render catalog."""
    path = root / "data" / "rme_sprite_backed_item_ids.json"
    try:
        payload = json.loads(path.read_text(encoding="ascii"))
        ids = {int(item_id) for item_id in payload["item_ids"] if int(item_id) > 0}
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return set(), "unavailable"
    if not ids:
        return set(), "unavailable"
    return ids, str(payload.get("source", "official_appearance_catalogs"))


@dataclass(frozen=True)
class WeightedItem:
    item_id: int
    chance: int


@dataclass(frozen=True)
class AutoBorder:
    border_id: int
    group: str | None
    edges: dict[str, int]

    def items_for_mask(self, same: dict[str, bool]) -> tuple[int, ...]:
        # GroundBrush::doBorders builds this mask from neighbors belonging to
        # the other ground family, in NW,N,NE,W,E,SW,S,SE bit order.
        mask = sum(
            1 << bit
            for bit, (key, _dx, _dy) in enumerate(RME_CONNECTED_OFFSETS)
            if not same[key]
        )
        return self.items_for_neighbor_mask(mask)

    def items_for_neighbor_mask(self, mask: int) -> tuple[int, ...]:
        output: list[int] = []
        diagonal_fallbacks = {
            "NORTHWEST_DIAGONAL": ("w", "n"),
            "NORTHEAST_DIAGONAL": ("e", "n"),
            "SOUTHWEST_DIAGONAL": ("s", "w"),
            "SOUTHEAST_DIAGONAL": ("s", "e"),
        }
        for symbol in RME_GROUND_BORDER_TABLE[mask]:
            item_id = self.edges.get(RME_BORDER_SYMBOL_TO_EDGE[symbol])
            if item_id is not None:
                output.append(item_id)
                continue
            for edge in diagonal_fallbacks.get(symbol, ()):
                fallback = self.edges.get(edge)
                if fallback is not None:
                    output.append(fallback)
        return tuple(output)

    def item_for_mask(self, same: dict[str, bool]) -> int | None:
        items = self.items_for_mask(same)
        return items[0] if items else None


@dataclass(frozen=True)
class GroundBorderRef:
    border_id: int
    align: str
    target_mode: str
    target_name: str | None = None

    def matches(self, other_name: str | None) -> bool:
        if self.target_mode == "all":
            return True
        if self.target_mode == "none":
            return other_name is None
        return other_name == self.target_name


@dataclass(frozen=True)
class GroundBrush:
    name: str
    items: tuple[WeightedItem, ...]
    outer_border_ids: tuple[int, ...]
    inner_border_ids: tuple[int, ...]
    optional_border_ids: tuple[int, ...]
    z_order: int = 0
    border_refs: tuple[GroundBorderRef, ...] = ()
    friends: frozenset[str] = frozenset()

    def choose_ground(self, x: int, y: int) -> int | None:
        return choose_weighted(self.items, x, y)

    def border_ref(self, align: str, other_name: str | None) -> GroundBorderRef | None:
        fallback = None
        for ref in self.border_refs:
            if ref.align != align:
                continue
            if ref.target_mode == "named" and ref.matches(other_name):
                return ref
            if ref.target_mode == "none" and other_name is None:
                return ref
            if ref.target_mode == "all" and fallback is None:
                fallback = ref
        return fallback

    def friend_of(self, other: "GroundBrush") -> bool:
        return other.name in self.friends


@dataclass(frozen=True)
class DoodadAlternative:
    items: tuple[WeightedItem, ...]
    composites: tuple[dict[tuple[int, int, int], tuple[int, ...]], ...]


@dataclass(frozen=True)
class DoodadBrush:
    name: str
    alternatives: tuple[DoodadAlternative, ...]

    @property
    def items(self) -> tuple[WeightedItem, ...]:
        return tuple(item for alternative in self.alternatives for item in alternative.items)

    @property
    def composites(self) -> tuple[dict[tuple[int, int, int], tuple[int, ...]], ...]:
        return tuple(composite for alternative in self.alternatives for composite in alternative.composites)

    def alternative(self, variation: int) -> DoodadAlternative | None:
        if not self.alternatives:
            return None
        return self.alternatives[variation % len(self.alternatives)]

    def choose_item(self, x: int, y: int, variation: int = 0) -> int | None:
        alternative = self.alternative(variation)
        return choose_weighted(alternative.items, x, y) if alternative else None


@dataclass(frozen=True)
class OrientedBrush:
    name: str
    kind: str
    variants: dict[str, tuple[int, ...]]

    def choose(self, align: str, x: int, y: int) -> int | None:
        item_ids = self.variants.get(align) or self.variants.get("center") or self.variants.get("horizontal")
        if not item_ids:
            return None
        return item_ids[stable_hash(x, y, self.name + align) % len(item_ids)]

    def choose_for_mask(self, same: dict[str, bool], x: int, y: int) -> int | None:
        table = RME_CONNECTED_ITEM_TABLES.get(self.kind)
        if table is None:
            align = align_from_mask(same)
        else:
            mask = sum(1 << bit for bit, (key, _dx, _dy) in enumerate(RME_CONNECTED_OFFSETS) if same[key])
            align = RME_CONNECTED_SYMBOL_TO_ALIGNMENT[table[mask]]
        return self.choose(align, x, y)


@dataclass(frozen=True)
class WallBrush:
    name: str
    variants: dict[str, tuple[WeightedItem, ...]]
    doors: dict[str, dict[str, tuple[int, ...]]]

    @property
    def owned_item_ids(self) -> frozenset[int]:
        return frozenset(
            [item.item_id for choices in self.variants.values() for item in choices]
            + [item_id for types in self.doors.values() for ids in types.values() for item_id in ids]
        )

    def choose(self, *, north: bool, south: bool, east: bool, west: bool, x: int = 0, y: int = 0) -> int | None:
        mask = int(north) | int(west) << 1 | int(east) << 2 | int(south) << 3
        full_alignment = RME_FULL_WALL_ALIGNMENTS[mask]
        item_id = self._variant(full_alignment, x, y)
        if item_id:
            return item_id
        return self._variant(RME_HALF_WALL_ALIGNMENTS[mask], x, y)

    def alignment_for_mask(self, *, north: bool, south: bool, east: bool, west: bool) -> str:
        mask = int(north) | int(west) << 1 | int(east) << 2 | int(south) << 3
        full = RME_FULL_WALL_ALIGNMENTS[mask]
        return full if self.variants.get(full) else RME_HALF_WALL_ALIGNMENTS[mask]

    def _variant(self, alignment: str, x: int, y: int) -> int | None:
        if alignment == "northwest diagonal":
            choices = self.variants.get(alignment) or self.variants.get("corner", ())
        else:
            choices = self.variants.get(alignment, ())
        return choose_weighted(choices, x, y)

    def choose_door(self, wall_type: str, door_type: str = "normal", x: int = 0, y: int = 0) -> int | None:
        candidates = self.doors.get(wall_type, {}).get(door_type)
        if not candidates:
            candidates = self.doors.get(wall_type, {}).get("archway")
        if not candidates:
            return None
        return candidates[stable_hash(x, y, self.name + wall_type + door_type) % len(candidates)]


class RMEBrushEngine:
    def __init__(
        self,
        ground_brushes: dict[str, GroundBrush],
        doodad_brushes: dict[str, DoodadBrush],
        wall_brushes: dict[str, WallBrush],
        table_brushes: dict[str, OrientedBrush],
        carpet_brushes: dict[str, OrientedBrush],
        wall_decoration_brushes: dict[str, OrientedBrush],
        borders: dict[int, AutoBorder],
        valid_base_ground: set[int],
        sprite_backed: set[int],
        sprite_certification_source: str = "classification",
        material_parse_errors: tuple[str, ...] = (),
    ) -> None:
        self.ground_brushes = ground_brushes
        self.doodad_brushes = doodad_brushes
        self.wall_brushes = wall_brushes
        self.table_brushes = table_brushes
        self.carpet_brushes = carpet_brushes
        self.wall_decoration_brushes = wall_decoration_brushes
        self.borders = borders
        self.valid_base_ground = valid_base_ground
        self.sprite_backed = sprite_backed
        self.sprite_certification_source = sprite_certification_source
        self.material_parse_errors = material_parse_errors

    @classmethod
    def load(cls, root: Path, classification: dict[str, Any]) -> "RMEBrushEngine":
        valid_base_ground = {int(i) for i in classification["categories"]["valid_base_ground"]}
        sprite_backed = {int(i) for i in classification["categories"].get("sprite_backed", [])}
        sprite_certification_source = "classification"
        if not sprite_backed:
            sprite_backed, sprite_certification_source = load_certified_sprite_backed_ids(root)
        materials_dir = resolve_materials_dir(root)
        borders = load_auto_borders(materials_dir)
        ground_brushes: dict[str, GroundBrush] = {}
        doodad_brushes: dict[str, DoodadBrush] = {}
        wall_brushes: dict[str, WallBrush] = {}
        table_brushes: dict[str, OrientedBrush] = {}
        carpet_brushes: dict[str, OrientedBrush] = {}
        wall_decoration_brushes: dict[str, OrientedBrush] = {}
        parse_errors: list[str] = []
        for path in sorted((materials_dir / "brushs").glob("*.xml")):
            xml_root = parse_material_xml(path)
            if xml_root is None:
                parse_errors.append(str(path))
                continue
            for elem in xml_root.findall("brush"):
                name = elem.attrib.get("name", "").strip().lower()
                brush_type = elem.attrib.get("type", "").strip().lower()
                if not name:
                    continue
                if brush_type == "ground":
                    # Canary's official GroundBrush membership is authoritative for
                    # fluid grounds whose server flags also expose trashholder behavior.
                    brush = parse_ground_brush(elem, valid_base_ground | sprite_backed)
                    if brush.items:
                        ground_brushes[name] = brush
                elif brush_type == "doodad":
                    brush = parse_doodad_brush(elem, sprite_backed)
                    if brush.items or brush.composites:
                        doodad_brushes[name] = brush
                elif brush_type == "wall":
                    brush = parse_wall_brush(elem, sprite_backed)
                    if brush.variants:
                        wall_brushes[name] = brush
                elif brush_type == "table":
                    brush = parse_oriented_brush(elem, "table", "table", sprite_backed)
                    if brush.variants:
                        table_brushes[name] = brush
                elif brush_type == "carpet":
                    brush = parse_oriented_brush(elem, "carpet", "carpet", sprite_backed)
                    if brush.variants:
                        carpet_brushes[name] = brush
                elif brush_type == "wall decoration":
                    brush = parse_wall_decoration_brush(elem, sprite_backed)
                    if brush.variants:
                        wall_decoration_brushes[name] = brush
        return cls(
            ground_brushes,
            doodad_brushes,
            wall_brushes,
            table_brushes,
            carpet_brushes,
            wall_decoration_brushes,
            borders,
            valid_base_ground,
            sprite_backed,
            sprite_certification_source,
            tuple(parse_errors),
        )

    def apply_ground_variants(
        self,
        grid: dict[tuple[int, int], dict[str, Any]],
        terrain_to_brush: dict[str, str],
    ) -> dict[str, Any]:
        changed = 0
        missing: set[str] = set()
        for (x, y), tile in grid.items():
            brush_name = terrain_to_brush.get(str(tile["terrain"]))
            if not brush_name:
                continue
            brush = self.ground_brushes.get(brush_name)
            if not brush:
                missing.add(brush_name)
                continue
            ground = brush.choose_ground(x, y)
            if ground:
                tile["ground"] = ground
                tile["brush"] = brush.name
                changed += 1
        return {"ground_variant_tiles": changed, "missing_ground_brushes": sorted(missing)}

    def apply_auto_borders(
        self,
        grid: dict[tuple[int, int], dict[str, Any]],
        terrain_to_brush: dict[str, str],
    ) -> dict[str, Any]:
        all_border_items = {
            item_id for border in self.borders.values() for item_id in border.edges.values()
        } | RME_GROUND_SPECIFIC_REPLACEMENT_IDS
        removed = 0
        for tile in grid.values():
            before = len(tile["items"])
            tile["items"] = [item_id for item_id in tile["items"] if item_id not in all_border_items]
            removed += before - len(tile["items"])
        applied = 0
        by_border: dict[int, int] = {}
        offsets = RME_CONNECTED_OFFSETS
        for (x, y), tile in list(grid.items()):
            brush = self.ground_brushes.get(terrain_to_brush.get(str(tile["terrain"]), ""))
            if not brush:
                continue
            clusters: dict[str | None, int] = {}
            for bit, (_key, dx, dy) in enumerate(offsets):
                neighbor = grid.get((x + dx, y + dy))
                other_name = (
                    terrain_to_brush.get(str(neighbor["terrain"]))
                    if neighbor is not None else None
                )
                if other_name == brush.name:
                    continue
                clusters[other_name] = clusters.get(other_name, 0) | (1 << bit)
            ordered_clusters = sorted(
                clusters.items(),
                key=lambda entry: self.ground_brushes.get(entry[0], brush).z_order,
            )
            for other_name, mask in ordered_clusters:
                other = self.ground_brushes.get(other_name or "")
                if other is not None and (brush.friend_of(other) or other.friend_of(brush)):
                    continue
                border_ref = self._ground_border_between(brush, other)
                if border_ref is None:
                    continue
                border = self.borders.get(border_ref.border_id)
                if not border:
                    continue
                item_ids = tuple(
                    item_id for item_id in border.items_for_neighbor_mask(mask)
                    if self.is_sprite_backed(item_id)
                )
                if item_ids:
                    tile["items"].extend(item_ids)
                    applied += len(item_ids)
                    by_border[border_ref.border_id] = by_border.get(border_ref.border_id, 0) + 1
        specific = self._apply_ground_specific_cases(grid)
        return {
            "autoborder_items": applied,
            "autoborder_items_replaced": removed,
            "autoborder_by_id": by_border,
            **specific,
        }

    @staticmethod
    def _apply_ground_specific_cases(
        grid: dict[tuple[int, int], dict[str, Any]],
    ) -> dict[str, int]:
        matched_cases = 0
        replaced_items = 0
        deleted_items = 0
        for tile in grid.values():
            for case in RME_GROUND_SPECIFIC_CASES:
                conditions = case["conditions"]
                if not all(
                    any(int(item_id) in condition["candidate_item_ids"] for item_id in tile["items"])
                    for condition in conditions
                ):
                    continue
                matched_cases += 1
                action = case["action"]
                if action["type"] == "delete_borders":
                    matched_ids = {
                        int(item_id)
                        for condition in conditions
                        for item_id in condition["candidate_item_ids"]
                    }
                    before = len(tile["items"])
                    tile["items"] = [item_id for item_id in tile["items"] if item_id not in matched_ids]
                    deleted_items += before - len(tile["items"])
                    continue
                target = int(action["target_item_id"])
                replacement = int(action["replacement_item_id"])
                for index, item_id in enumerate(tile["items"]):
                    if int(item_id) == target:
                        tile["items"][index] = replacement
                        replaced_items += 1
                        break
                # GroundBrush::doBorders returns after a replacement action.
                break
        return {
            "ground_specific_cases_matched": matched_cases,
            "ground_specific_items_replaced": replaced_items,
            "ground_specific_items_deleted": deleted_items,
        }

    @staticmethod
    def _ground_border_between(first: GroundBrush, second: GroundBrush | None) -> GroundBorderRef | None:
        second_name = second.name if second is not None else None
        if second is None:
            return first.border_ref("inner", None)
        if first.z_order < second.z_order and second.outer_border_ids:
            inner = first.border_ref("inner", second_name)
            if inner is not None:
                return inner
            return second.border_ref("outer", first.name)
        return first.border_ref("inner", second_name)

    def apply_optional_borders(
        self,
        grid: dict[tuple[int, int], dict[str, Any]],
        terrain_to_brush: dict[str, str],
        *,
        modulo: int | None = None,
    ) -> dict[str, Any]:
        optional_item_ids = {
            item_id
            for brush in self.ground_brushes.values()
            for border_id in brush.optional_border_ids
            for border in (self.borders.get(border_id),)
            if border is not None
            for item_id in border.edges.values()
        }
        removed = 0
        for tile in grid.values():
            if not bool(tile.get("optional_border", False)):
                continue
            before = len(tile["items"])
            tile["items"] = [item_id for item_id in tile["items"] if item_id not in optional_item_ids]
            removed += before - len(tile["items"])
        applied = 0
        rejected = 0
        for (x, y), tile in list(grid.items()):
            if not bool(tile.get("optional_border", False)):
                continue
            current_name = terrain_to_brush.get(str(tile["terrain"]), "")
            current = self.ground_brushes.get(current_name)
            if current is not None and current.optional_border_ids:
                # OptionalBorderBrush::canDraw forbids marking the mountain
                # family itself; the flag belongs to an adjacent support tile.
                rejected += 1
                continue
            clusters: dict[str, int] = {}
            for bit, (_key, dx, dy) in enumerate(RME_CONNECTED_OFFSETS):
                neighbor = grid.get((x + dx, y + dy))
                if neighbor is None:
                    continue
                other_name = terrain_to_brush.get(str(neighbor["terrain"]), "")
                other = self.ground_brushes.get(other_name)
                if other is None or not other.optional_border_ids:
                    continue
                clusters[other_name] = clusters.get(other_name, 0) | (1 << bit)
            if not clusters:
                rejected += 1
                continue
            for other_name, mask in clusters.items():
                other = self.ground_brushes[other_name]
                for border_id in other.optional_border_ids:
                    border = self.borders.get(border_id)
                    if not border:
                        continue
                    item_ids = tuple(
                        item_id for item_id in border.items_for_neighbor_mask(mask)
                        if self.is_sprite_backed(item_id)
                    )
                    if item_ids:
                        tile["items"].extend(item_ids)
                        applied += len(item_ids)
                        break
        return {
            "optional_border_items": applied,
            "optional_border_items_replaced": removed,
            "optional_border_rejected_tiles": rejected,
            "selection_policy": "explicit_tile_flag",
            "legacy_random_modulo_ignored": modulo is not None,
        }

    @staticmethod
    def mark_optional_borders(
        grid: dict[tuple[int, int], dict[str, Any]],
        positions: list[tuple[int, int]] | tuple[tuple[int, int], ...],
        enabled: bool = True,
    ) -> int:
        changed = 0
        for position in positions:
            tile = grid.get((int(position[0]), int(position[1])))
            if tile is None:
                continue
            if bool(tile.get("optional_border", False)) == enabled:
                continue
            tile["optional_border"] = enabled
            changed += 1
        return changed

    def apply_doodads(
        self,
        grid: dict[tuple[int, int], dict[str, Any]],
        plans: list[dict[str, Any]],
    ) -> dict[str, Any]:
        applied = 0
        missing: set[str] = set()
        for plan in plans:
            brush = self.doodad_brushes.get(str(plan["brush"]).lower())
            if not brush:
                missing.add(str(plan["brush"]))
                continue
            terrains = set(plan.get("terrains") or [])
            modulo = int(plan.get("modulo", 29))
            residue = int(plan.get("residue", 0))
            max_count = int(plan.get("max_count", 999999))
            requested_variation = plan.get("variation")
            count = 0
            for (x, y), tile in sorted(grid.items()):
                if terrains and tile["terrain"] not in terrains:
                    continue
                if stable_hash(x, y, brush.name) % modulo != residue:
                    continue
                variation = (
                    int(requested_variation)
                    if requested_variation is not None
                    else stable_hash(x, y, brush.name + ":variation") % max(1, len(brush.alternatives))
                )
                alternative = brush.alternative(variation)
                item_id = brush.choose_item(x, y, variation)
                if item_id and self.is_sprite_backed(item_id):
                    tile["items"].append(item_id)
                    applied += 1
                    count += 1
                elif alternative and alternative.composites:
                    composite = alternative.composites[
                        stable_hash(x, y, brush.name + ":composite") % len(alternative.composites)
                    ]
                    placed = 0
                    for (dx, dy, _dz), composite_item_ids in composite.items():
                        target = grid.get((x + dx, y + dy))
                        if target is None:
                            continue
                        certified = [item_id for item_id in composite_item_ids if self.is_sprite_backed(item_id)]
                        target["items"].extend(certified)
                        placed += len(certified)
                    if placed:
                        applied += placed
                        count += 1
                if count >= max_count:
                    break
        return {"doodad_items": applied, "missing_doodad_brushes": sorted(missing)}

    def apply_walls(
        self,
        grid: dict[tuple[int, int], dict[str, Any]],
        plans: list[dict[str, Any]],
    ) -> dict[str, Any]:
        applied = 0
        replaced = 0
        missing: set[str] = set()
        for plan in plans:
            name = str(plan["brush"]).lower()
            brush = self.wall_brushes.get(name)
            if brush is None:
                missing.add(name)
                continue
            positions = {tuple(map(int, position)) for position in plan.get("positions", [])}
            doors = {tuple(map(int, position)) for position in plan.get("doors", [])}
            door_type = str(plan.get("door_type", "normal"))
            owned = brush.owned_item_ids
            for x, y in sorted(positions):
                tile = grid.get((x, y))
                if tile is None:
                    continue
                before = len(tile["items"])
                tile["items"] = [item_id for item_id in tile["items"] if item_id not in owned]
                replaced += before - len(tile["items"])
                north = (x, y - 1) in positions
                south = (x, y + 1) in positions
                east = (x + 1, y) in positions
                west = (x - 1, y) in positions
                if (x, y) in doors:
                    wall_type = "horizontal" if east or west else "vertical"
                    item_id = brush.choose_door(wall_type, door_type, x, y)
                else:
                    item_id = brush.choose(north=north, south=south, east=east, west=west, x=x, y=y)
                if item_id and self.is_sprite_backed(item_id):
                    tile["items"].append(item_id)
                    applied += 1
        return {
            "wall_items": applied,
            "wall_items_replaced": replaced,
            "missing_wall_brushes": sorted(missing),
        }

    def erase_brush(
        self,
        grid: dict[tuple[int, int], dict[str, Any]],
        positions: list[tuple[int, int]],
        *,
        terrain_to_brush: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Erase overlays and regenerate neighboring RME borders."""
        border_items = {
            item_id for border in self.borders.values() for item_id in border.edges.values()
        }
        removed = 0
        touched = set(positions)
        for x, y in positions:
            tile = grid.get((x, y))
            if tile is None:
                continue
            before = len(tile["items"])
            tile["items"] = []
            removed += before
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    touched.add((x + dx, y + dy))
        for position in touched:
            tile = grid.get(position)
            if tile is not None:
                tile["items"] = [item_id for item_id in tile["items"] if item_id not in border_items]
        rebuilt = 0
        if terrain_to_brush:
            rebuilt = int(self.apply_auto_borders(grid, terrain_to_brush)["autoborder_items"])
        return {"erased_items": removed, "border_items_rebuilt": rebuilt, "dirty_positions": len(touched)}

    def audit(self) -> dict[str, Any]:
        return {
            "ground_brushes": len(self.ground_brushes),
            "doodad_brushes": len(self.doodad_brushes),
            "wall_brushes": len(self.wall_brushes),
            "table_brushes": len(self.table_brushes),
            "carpet_brushes": len(self.carpet_brushes),
            "wall_decoration_brushes": len(self.wall_decoration_brushes),
            "auto_borders": len(self.borders),
            "connected_item_mask_tables": {
                "table": len(RME_CONNECTED_ITEM_TABLES["table"]),
                "carpet": len(RME_CONNECTED_ITEM_TABLES["carpet"]),
            },
            "ground_border_mask_table": len(RME_GROUND_BORDER_TABLE),
            "ground_specific_cases": len(RME_GROUND_SPECIFIC_CASES),
            "sprite_backed_filter": bool(self.sprite_backed),
            "sprite_backed_items": len(self.sprite_backed),
            "sprite_certification_source": self.sprite_certification_source,
            "material_parse_errors": list(self.material_parse_errors),
            "systems": [
                "ground", "autoborder", "optional_border", "wall", "door", "doodad",
                "multitile_composite", "table", "carpet", "wall_decoration", "erase_reborder",
            ],
        }

    def apply_oriented_items(
        self,
        grid: dict[tuple[int, int], dict[str, Any]],
        plans: list[dict[str, Any]],
    ) -> dict[str, Any]:
        applied = 0
        missing: set[str] = set()
        for plan in plans:
            kind = str(plan["kind"])
            collection = {
                "table": self.table_brushes,
                "carpet": self.carpet_brushes,
                "wall_decoration": self.wall_decoration_brushes,
            }.get(kind, {})
            brush = collection.get(str(plan["brush"]).lower())
            if not brush:
                missing.add(f"{kind}:{plan['brush']}")
                continue
            positions = [tuple(pos) for pos in plan.get("positions", [])]
            terrains = set(plan.get("terrains") or [])
            if not positions:
                modulo = int(plan.get("modulo", 31))
                residue = int(plan.get("residue", 0))
                max_count = int(plan.get("max_count", 999999))
                positions = [
                    pos for pos, tile in sorted(grid.items())
                    if (not terrains or tile["terrain"] in terrains)
                    and stable_hash(pos[0], pos[1], brush.name) % modulo == residue
                ][:max_count]
            for x, y in positions:
                tile = grid.get((int(x), int(y)))
                if not tile:
                    continue
                align = str(plan.get("align", "center"))
                if align == "auto":
                    same = neighborhood_same_terrain(grid, int(x), int(y), terrains or {tile["terrain"]})
                    item_id = brush.choose_for_mask(same, int(x), int(y))
                else:
                    item_id = brush.choose(align, int(x), int(y))
                if item_id and self.is_sprite_backed(item_id):
                    tile["items"].append(item_id)
                    applied += 1
        return {"oriented_items": applied, "missing_oriented_brushes": sorted(missing)}

    def wall_brush(self, name: str) -> WallBrush | None:
        return self.wall_brushes.get(name.lower())

    def is_sprite_backed(self, item_id: int) -> bool:
        return not self.sprite_backed or item_id in self.sprite_backed


def load_auto_borders(materials_dir: Path) -> dict[int, AutoBorder]:
    borders: dict[int, AutoBorder] = {}
    paths = sorted((materials_dir / "borders").glob("*.xml")) + [materials_dir / "borders.xml"]
    for path in paths:
        if not path.exists():
            continue
        xml_root = parse_material_xml(path)
        if xml_root is None:
            continue
        for elem in xml_root.iter("border"):
            border_id = to_int(elem.attrib.get("id"))
            if border_id is None:
                continue
            edges: dict[str, int] = {}
            for child in elem.iter("borderitem"):
                edge = child.attrib.get("edge", "")
                item_id = to_int(child.attrib.get("item"))
                if edge and item_id:
                    edges[edge] = item_id
            if edges:
                borders[border_id] = AutoBorder(border_id, elem.attrib.get("group"), edges)
    return borders


def parse_ground_brush(elem: ET.Element, valid_base_ground: set[int]) -> GroundBrush:
    items = tuple(
        WeightedItem(item_id, chance)
        for item_id, chance in parse_weighted_items(elem, recursive=False)
        if chance > 0 and item_id in valid_base_ground
    )
    outer: list[int] = []
    inner: list[int] = []
    border_refs: list[GroundBorderRef] = []
    for border in elem.findall("border"):
        border_id = to_int(border.attrib.get("id"))
        if border_id is None:
            continue
        align = border.attrib.get("align", "outer").strip().lower()
        target_value = border.attrib.get("to")
        if target_value is None or target_value.strip().lower() == "all":
            target_mode = "all"
            target_name = None
        elif target_value.strip().lower() == "none":
            target_mode = "none"
            target_name = None
        else:
            target_mode = "named"
            target_name = target_value.strip().lower()
        border_refs.append(GroundBorderRef(border_id, align, target_mode, target_name))
        if align == "inner":
            inner.append(border_id)
        else:
            outer.append(border_id)
    optional = tuple(
        border_id
        for opt in elem.findall("optional")
        for border_id in [to_int(opt.attrib.get("id"))]
        if border_id is not None
    )
    friends = frozenset(
        child.attrib.get("name", "").strip().lower()
        for child in elem.findall("friend")
        if child.attrib.get("name", "").strip()
    )
    return GroundBrush(
        elem.attrib.get("name", "").strip().lower(),
        items,
        tuple(outer),
        tuple(inner),
        optional,
        to_int(elem.attrib.get("z-order")) or 0,
        tuple(border_refs),
        friends,
    )


def parse_doodad_brush(elem: ET.Element, sprite_backed: set[int]) -> DoodadBrush:
    def parse_alternative(node: ET.Element) -> DoodadAlternative:
        items = tuple(
            WeightedItem(item_id, chance)
            for item_id, chance in parse_weighted_items(node, recursive=False)
            if chance > 0 and (not sprite_backed or item_id in sprite_backed)
        )
        composites: list[dict[tuple[int, int, int], tuple[int, ...]]] = []
        for composite in node.findall("composite"):
            tiles: dict[tuple[int, int, int], tuple[int, ...]] = {}
            for tile in composite.findall("tile"):
                item_ids = tuple(
                    item_id
                    for item_id, _chance in parse_weighted_items(tile, recursive=False)
                    if not sprite_backed or item_id in sprite_backed
                )
                if item_ids:
                    tiles[
                        (
                            to_int(tile.attrib.get("x")) or 0,
                            to_int(tile.attrib.get("y")) or 0,
                            to_int(tile.attrib.get("z")) or 0,
                        )
                    ] = item_ids
            if tiles:
                composites.append(tiles)
        return DoodadAlternative(items, tuple(composites))

    alternatives = [parse_alternative(node) for node in elem.findall("alternate")]
    direct = parse_alternative(elem)
    if alternatives:
        # DoodadBrush::loadAlternative appends direct root entries to the last
        # explicit alternative when alternatives already exist.
        if direct.items or direct.composites:
            tail = alternatives[-1]
            alternatives[-1] = DoodadAlternative(
                tail.items + direct.items,
                tail.composites + direct.composites,
            )
    else:
        alternatives.append(direct)
    return DoodadBrush(
        elem.attrib.get("name", "").strip().lower(),
        tuple(alternative for alternative in alternatives if alternative.items or alternative.composites),
    )


def parse_wall_brush(elem: ET.Element, sprite_backed: set[int]) -> WallBrush:
    variants: dict[str, tuple[WeightedItem, ...]] = {}
    doors: dict[str, dict[str, list[int]]] = {}
    for wall in elem.findall("wall"):
        wall_type = wall.attrib.get("type")
        if not wall_type:
            continue
        weighted = tuple(
            WeightedItem(item_id, chance)
            for item_id, chance in parse_weighted_items(wall, recursive=False)
            if chance > 0 and (not sprite_backed or item_id in sprite_backed)
        )
        if weighted:
            variants[wall_type] = weighted
        for door in wall.findall("door"):
            item_id = to_int(door.attrib.get("id"))
            door_type = str(door.attrib.get("type", "normal")).split()[0]
            if item_id and (not sprite_backed or item_id in sprite_backed):
                doors.setdefault(wall_type, {}).setdefault(door_type, []).append(item_id)
    frozen_doors = {
        wall_type: {door_type: tuple(ids) for door_type, ids in door_types.items()}
        for wall_type, door_types in doors.items()
    }
    return WallBrush(elem.attrib.get("name", "").strip().lower(), variants, frozen_doors)


def parse_oriented_brush(elem: ET.Element, kind: str, child_name: str, sprite_backed: set[int]) -> OrientedBrush:
    variants: dict[str, list[int]] = {}
    for child in elem.findall(child_name):
        align = child.attrib.get("align", "center")
        ids: list[int] = []
        item_id = to_int(child.attrib.get("id"))
        if item_id:
            ids.append(item_id)
        for item in child.findall("item"):
            nested_id = to_int(item.attrib.get("id"))
            if nested_id:
                ids.append(nested_id)
        for candidate in ids:
            if not sprite_backed or candidate in sprite_backed:
                variants.setdefault(align, []).append(candidate)
    return OrientedBrush(
        elem.attrib.get("name", "").strip().lower(),
        kind,
        {align: tuple(ids) for align, ids in variants.items()},
    )


def parse_wall_decoration_brush(elem: ET.Element, sprite_backed: set[int]) -> OrientedBrush:
    variants: dict[str, list[int]] = {}
    for wall in elem.findall("wall"):
        wall_type = wall.attrib.get("type", "horizontal")
        for item in wall.findall("item"):
            item_id = to_int(item.attrib.get("id"))
            if item_id and (not sprite_backed or item_id in sprite_backed):
                variants.setdefault(wall_type, []).append(item_id)
    return OrientedBrush(
        elem.attrib.get("name", "").strip().lower(),
        "wall_decoration",
        {align: tuple(ids) for align, ids in variants.items()},
    )


def parse_weighted_items(elem: ET.Element, *, recursive: bool) -> list[tuple[int, int]]:
    items = elem.iter("item") if recursive else elem.findall("item")
    out: list[tuple[int, int]] = []
    for item in items:
        item_id = to_int(item.attrib.get("id"))
        chance = to_int(item.attrib.get("chance"))
        if item_id is not None:
            out.append((item_id, 1 if chance is None else chance))
    return out


def parse_material_xml(path: Path) -> ET.Element | None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#\\d+;|#x[0-9a-fA-F]+;)", "&amp;", text)
    try:
        return ET.fromstring(text)
    except ET.ParseError:
        return None


def choose_weighted(items: tuple[WeightedItem, ...], x: int, y: int) -> int | None:
    total = sum(max(0, item.chance) for item in items)
    if total <= 0:
        return None
    pick = stable_hash(x, y, str(total)) % total
    running = 0
    for item in items:
        running += max(0, item.chance)
        if pick < running:
            return item.item_id
    return items[-1].item_id


def same_brush(
    grid: dict[tuple[int, int], dict[str, Any]],
    terrain_to_brush: dict[str, str],
    x: int,
    y: int,
    dx: int,
    dy: int,
) -> bool:
    tile = grid.get((x, y))
    other = grid.get((x + dx, y + dy))
    if not tile or not other:
        return False
    return terrain_to_brush.get(str(tile["terrain"])) == terrain_to_brush.get(str(other["terrain"]))


def neighborhood_same_terrain(
    grid: dict[tuple[int, int], dict[str, Any]],
    x: int,
    y: int,
    terrains: set[str],
) -> dict[str, bool]:
    def same(dx: int, dy: int) -> bool:
        other = grid.get((x + dx, y + dy))
        return bool(other and other["terrain"] in terrains)

    return {
        "n": same(0, -1),
        "e": same(1, 0),
        "s": same(0, 1),
        "w": same(-1, 0),
        "nw": same(-1, -1),
        "ne": same(1, -1),
        "sw": same(-1, 1),
        "se": same(1, 1),
    }


def align_from_mask(same: dict[str, bool]) -> str:
    if not same["n"] and not same["w"]:
        return "cnw"
    if not same["n"] and not same["e"]:
        return "cne"
    if not same["s"] and not same["w"]:
        return "csw"
    if not same["s"] and not same["e"]:
        return "cse"
    if not same["n"]:
        return "n"
    if not same["e"]:
        return "e"
    if not same["s"]:
        return "s"
    if not same["w"]:
        return "w"
    if same["n"] and same["w"] and not same["nw"]:
        return "dnw"
    if same["n"] and same["e"] and not same["ne"]:
        return "dne"
    if same["s"] and same["w"] and not same["sw"]:
        return "dsw"
    if same["s"] and same["e"] and not same["se"]:
        return "dse"
    return "center"


def stable_hash(x: int, y: int, salt: str) -> int:
    value = (x * 73856093) ^ (y * 19349663) ^ (len(salt) * 83492791)
    for char in salt:
        value = ((value << 5) - value + ord(char)) & 0xFFFFFFFF
    return value & 0x7FFFFFFF


def to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
