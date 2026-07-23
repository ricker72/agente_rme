from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.opentibia.assets.appearance_dat_flags import AppearanceDatFlagExtractor


@dataclass(frozen=True)
class RMEItemType:
    item_id: int
    name: str = ""
    client_id: int | None = None
    always_on_bottom: bool = False
    always_on_top_order: int = 0
    ground_equivalent: int = 0
    is_ground: bool = False
    is_border: bool = False
    is_wall: bool = False
    is_table: bool = False
    is_carpet: bool = False
    is_door: bool = False
    is_container: bool = False
    is_teleport: bool = False
    is_depot: bool = False
    is_meta: bool = False
    unpassable: bool = False
    pickupable: bool = False
    moveable: bool = True
    stackable: bool = False
    block_missiles: bool = False
    block_pathfinder: bool = False
    has_elevation: bool = False
    exact_flags: tuple[str, ...] = ()
    flag_source: str = "unknown"
    raw_attributes: tuple[str, ...] = ()


class RMEItemTypeCatalog:
    def __init__(self, items: dict[int, RMEItemType] | None = None) -> None:
        self.items = items or {}

    @classmethod
    def load(
        cls,
        root: str | Path = ".",
        *,
        appearances_path: str | Path | None = None,
        material_root: str | Path | None = None,
    ) -> "RMEItemTypeCatalog":
        base = Path(root)
        exact = _load_canary_protobuf_item_types(
            base,
            Path(appearances_path) if appearances_path is not None else None,
        )
        if exact:
            _apply_game_xml_exact(base, exact)
            _apply_source_role_hints(base, exact, material_root=material_root)
            return cls(exact)
        items_xml = _first_existing(
            [
                base / "projects" / "materials" / "items.xml",
                base / "projects" / "canary-extracted" / "canary-map-editor-v4.0-windows" / "data" / "items" / "items.xml",
                base / "data" / "items" / "items.xml",
            ]
        )
        items: dict[int, RMEItemType] = {}
        if items_xml is not None:
            items.update(_load_items_xml(items_xml))
        _apply_source_role_hints(base, items, material_root=material_root)
        _apply_generated_ground_hints(base, items)
        return cls(items)

    def get(self, item_id: int) -> RMEItemType:
        item_id = int(item_id)
        return self.items.get(item_id, RMEItemType(item_id=item_id))

    def classify_stack(self, item_ids: Iterable[int]) -> tuple[int | None, list[int]]:
        ground: int | None = None
        rest: list[int] = []
        for item_id in item_ids:
            item = self.get(int(item_id))
            if item.is_ground:
                ground = item.item_id
            elif item.ground_equivalent and ground is None:
                ground = item.ground_equivalent
                rest.append(item.item_id)
            else:
                rest.append(item.item_id)
        return ground, self.sort_items(rest)

    def sort_items(self, item_ids: Iterable[int]) -> list[int]:
        # Canary Tile::addItem/findBottomInsertPosition: bottom items are inserted
        # by topOrder; every other item preserves insertion order.
        ordered: list[int] = []
        for raw_id in item_ids:
            item_id = int(raw_id)
            item = self.get(item_id)
            if item.ground_equivalent:
                ordered.insert(0, item_id)
                continue
            if not item.always_on_bottom:
                ordered.append(item_id)
                continue
            index = len(ordered)
            for candidate_index, candidate_id in enumerate(ordered):
                candidate = self.get(candidate_id)
                if (
                    not candidate.always_on_bottom
                    or item.always_on_top_order < candidate.always_on_top_order
                ):
                    index = candidate_index
                    break
            ordered.insert(index, item_id)
        return ordered

    def audit(self) -> dict[str, object]:
        role_counts = {
            "ground": sum(1 for item in self.items.values() if item.is_ground),
            "border": sum(1 for item in self.items.values() if item.is_border),
            "wall": sum(1 for item in self.items.values() if item.is_wall),
            "table": sum(1 for item in self.items.values() if item.is_table),
            "carpet": sum(1 for item in self.items.values() if item.is_carpet),
            "ground_equivalent": sum(1 for item in self.items.values() if item.ground_equivalent),
        }
        return {
            "item_type_catalog_ready": bool(self.items),
            "item_count": len(self.items),
            "role_counts": role_counts,
            "exact_canary_flag_items": sum(
                item.flag_source == "appearances.dat:Canary loadFromProtobuf"
                for item in self.items.values()
            ),
            "certified": any(
                item.flag_source == "appearances.dat:Canary loadFromProtobuf"
                for item in self.items.values()
            ),
            "name_inference_used": any(item.flag_source == "items.xml:name_inference" for item in self.items.values()),
        }


def _load_canary_protobuf_item_types(
    base: Path,
    appearances_path: Path | None = None,
) -> dict[int, RMEItemType]:
    appearances = appearances_path or (
        base / "assets" / "appearances-ee339aff5b3cb38289287ff25cec261d8d2790e6e146938d4dfd9f138b065980.dat"
    )
    render_catalog_path = base / "APPEARANCE_RENDER_CATALOG.json"
    if not appearances.exists() or not render_catalog_path.exists():
        return {}
    try:
        render_catalog = json.loads(render_catalog_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    extractor = AppearanceDatFlagExtractor(appearances)
    items: dict[int, RMEItemType] = {}
    for raw_id, entry in render_catalog.items():
        if not str(raw_id).isdigit() or not isinstance(entry, dict):
            continue
        item_id = int(raw_id)
        exact = extractor.extract_from_catalog_entry(item_id, entry)
        flags = exact.flags
        clip = bool(flags.get("clip"))
        top = bool(flags.get("top"))
        bottom = bool(flags.get("bottom"))
        top_order = 1 if clip else 3 if top else 2 if bottom else 0
        items[item_id] = RMEItemType(
            item_id=item_id,
            client_id=item_id,
            always_on_bottom=clip or top or bottom,
            always_on_top_order=top_order,
            is_ground="waypoints" in flags,
            is_container=bool(flags.get("container")),
            unpassable=bool(flags.get("unpass")),
            pickupable=bool(flags.get("take")),
            moveable=not bool(flags.get("unmove")),
            stackable=bool(flags.get("cumulative")),
            block_missiles=bool(flags.get("unsight")),
            block_pathfinder=bool(flags.get("avoid")),
            has_elevation="elevation" in flags,
            exact_flags=exact.exact_fields,
            flag_source="appearances.dat:Canary loadFromProtobuf",
        )
    return items


def _apply_game_xml_exact(base: Path, items: dict[int, RMEItemType]) -> None:
    path = _first_existing(
        [
            base / "projects" / "canary-extracted" / "canary-map-editor-v4.0-windows" / "data" / "items" / "items.xml",
            base / "projects" / "materials" / "items.xml",
        ]
    )
    if path is None:
        return
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return
    for element in root.findall(".//item"):
        first = element.get("id") or element.get("fromid")
        last = element.get("id") or element.get("toid") or first
        if not first or not last or not first.isdigit() or not last.isdigit():
            continue
        attrs = {attr.get("key", "").lower(): attr.get("value", "") for attr in element.findall("attribute")}
        explicit_type = attrs.get("type", "").lower()
        for item_id in range(int(first), int(last) + 1):
            current = items.get(item_id, RMEItemType(item_id=item_id))
            data = current.__dict__.copy()
            data["name"] = element.get("name") or current.name
            data["is_container"] = current.is_container or "containersize" in attrs
            data["is_teleport"] = explicit_type == "teleport"
            data["is_depot"] = explicit_type == "depot"
            data["is_door"] = explicit_type == "door"
            data["raw_attributes"] = tuple(
                f"{key}={value}" for key, value in sorted(attrs.items()) if key
            )
            items[item_id] = RMEItemType(**data)


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _bool_value(value: str | None) -> bool:
    return str(value or "").lower() in {"1", "true", "yes"}


def _load_items_xml(path: Path) -> dict[int, RMEItemType]:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return {}
    items: dict[int, RMEItemType] = {}
    for element in root.findall(".//item"):
        raw_id = element.get("id")
        if not raw_id or not raw_id.isdigit():
            continue
        item_id = int(raw_id)
        attrs = {attr.get("key", "").lower(): attr.get("value", "") for attr in element.findall("attribute")}
        raw_attributes = tuple(f"{key}={value}" for key, value in sorted(attrs.items()) if key)
        name = element.get("name") or ""
        lowered = " ".join([name.lower(), " ".join(raw_attributes).lower()])
        items[item_id] = RMEItemType(
            item_id=item_id,
            name=name,
            client_id=_int_or_none(attrs.get("clientid") or attrs.get("client_id")),
            always_on_bottom=_bool_value(attrs.get("alwaysonbottom") or attrs.get("always_on_bottom")),
            always_on_top_order=int(attrs.get("alwaysontoporder") or attrs.get("always_on_top_order") or 0),
            ground_equivalent=int(attrs.get("groundequivalent") or attrs.get("ground_equivalent") or 0),
            is_ground=_bool_value(attrs.get("ground")) or "ground" in lowered or "floor" in lowered,
            is_border=_bool_value(attrs.get("border")) or "border" in lowered,
            is_wall=_bool_value(attrs.get("wall")) or "wall" in lowered,
            is_table=_bool_value(attrs.get("table")) or "table" in lowered,
            is_carpet=_bool_value(attrs.get("carpet")) or "carpet" in lowered,
            is_door=_bool_value(attrs.get("door")) or "door" in lowered,
            is_container=_bool_value(attrs.get("container")) or "container" in lowered,
            is_teleport=_bool_value(attrs.get("teleport")) or "teleport" in lowered,
            is_depot=_bool_value(attrs.get("depot")) or "depot" in lowered,
            is_meta=_bool_value(attrs.get("meta")) or "meta" in lowered,
            unpassable=_bool_value(attrs.get("unpassable") or attrs.get("blocksolid")),
            pickupable=_bool_value(attrs.get("pickupable")),
            raw_attributes=raw_attributes,
        )
    return items


def _apply_source_role_hints(
    base: Path,
    items: dict[int, RMEItemType],
    *,
    material_root: str | Path | None = None,
) -> None:
    materials = _first_existing(
        [
            Path(material_root) if material_root is not None else base / "__missing_material_root__",
            base / "projects" / "materials",
            base / "projects" / "canary-extracted" / "canary-map-editor-v4.0-windows" / "data" / "materials",
            base / "resources" / "materials",
        ]
    )
    if materials is None:
        return
    role_by_type = {
        "ground": "is_ground",
        "wall": "is_wall",
        "table": "is_table",
        "carpet": "is_carpet",
        "border": "is_border",
    }
    for path in sorted((materials / "brushs").glob("*.xml")):
        root = _parse_material_xml(path)
        if root is None:
            continue
        for brush in root.findall(".//brush"):
            brush_type = (brush.get("type") or "").strip().lower()
            field = role_by_type.get(brush_type)
            if field is None:
                continue
            for item_element in brush.findall(".//*[@id]"):
                raw_id = item_element.get("id")
                if not raw_id or not raw_id.isdigit():
                    continue
                item_id = int(raw_id)
                current = items.get(item_id, RMEItemType(item_id=item_id))
                items[item_id] = _replace_flag(current, field)
            if brush_type == "wall":
                for door_element in brush.findall(".//door[@id]"):
                    raw_id = door_element.get("id")
                    if not raw_id or not raw_id.isdigit():
                        continue
                    item_id = int(raw_id)
                    current = items.get(item_id, RMEItemType(item_id=item_id))
                    items[item_id] = _replace_flag(_replace_flag(current, "is_wall"), "is_door")
    for path in sorted((materials / "borders").glob("*.xml")) + [materials / "borders.xml"]:
        if not path.exists():
            continue
        root = _parse_material_xml(path)
        if root is None:
            continue
        for border_item in root.findall(".//borderitem[@item]"):
            raw_id = border_item.get("item")
            if not raw_id or not raw_id.isdigit():
                continue
            item_id = int(raw_id)
            current = items.get(item_id, RMEItemType(item_id=item_id))
            items[item_id] = _replace_flag(current, "is_border")


def _parse_material_xml(path: Path) -> ET.Element | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)", "&amp;", text)
    try:
        return ET.fromstring(text)
    except ET.ParseError:
        return None


def _apply_generated_ground_hints(base: Path, items: dict[int, RMEItemType]) -> None:
    for item_id in sorted(_load_ground_hint_ids(base)):
        current = items.get(item_id, RMEItemType(item_id=item_id))
        if current.is_border or current.is_wall or current.is_table or current.is_carpet or current.pickupable:
            continue
        items[item_id] = _replace_flag(current, "is_ground")


def _load_ground_hint_ids(base: Path) -> set[int]:
    out: set[int] = set()
    for path in (
        base / "exports" / "WG18H_TILE_MATERIALIZATION_AUDIT.json",
        base / "exports" / "RME_MATERIAL_CLASSIFICATION.json",
        base / "exports" / "WG18H_RME_MATERIAL_CLASSIFICATION.json",
    ):
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for raw_id in data.get("unique_base_ground_ids") or []:
            if isinstance(raw_id, int) or str(raw_id).isdigit():
                out.add(int(raw_id))
        categories = data.get("categories") if isinstance(data, dict) else None
        if isinstance(categories, dict):
            for raw_id in categories.get("valid_base_ground") or []:
                if isinstance(raw_id, int) or str(raw_id).isdigit():
                    out.add(int(raw_id))
            invalid = {int(raw_id) for raw_id in categories.get("invalid_for_ground") or [] if isinstance(raw_id, int) or str(raw_id).isdigit()}
            out -= invalid
    return out


def _replace_flag(item: RMEItemType, field: str) -> RMEItemType:
    data = item.__dict__.copy()
    data[field] = True
    if field == "is_border":
        data["always_on_bottom"] = True
    return RMEItemType(**data)


def _int_or_none(value: str | None) -> int | None:
    if value and str(value).isdigit():
        return int(value)
    return None
