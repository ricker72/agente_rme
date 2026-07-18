"""Load Canary/RME item and brush material XML into normalized records."""

from __future__ import annotations

import xml.etree.ElementTree as ET
import re
from pathlib import Path

from .asset_database import OpenTibiaAsset, OpenTibiaBrush


def _parse_xml(path: Path) -> ET.Element:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as strict_error:
        try:
            source = path.read_text(encoding="utf-8-sig")
            source = re.sub(
                r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9A-Fa-f]+;)",
                "&amp;",
                source,
            )
            source = re.sub(
                r"<!--(.*?)-->",
                lambda match: "<!--" + match.group(1).replace("--", "- -") + "-->",
                source,
                flags=re.DOTALL,
            )
            return ET.fromstring(source)
        except (OSError, UnicodeError, ET.ParseError) as recovery_error:
            raise ValueError(
                f"parse error: {path}: strict={strict_error}; recovery={recovery_error}"
            ) from recovery_error


def _category_from_name(name: str, fallback: str = "Raw Items") -> str:
    lowered = name.lower()
    rules = [
        ("venore", "Buildings"),
        ("wall", "Walls"),
        ("floor", "Grounds"),
        ("grass", "Grounds"),
        ("swamp", "Water"),
        ("water", "Water"),
        ("sea", "Water"),
        ("bridge", "Roads"),
        ("road", "Roads"),
        ("tree", "Nature"),
        ("plant", "Nature"),
        ("wood", "Furniture"),
        ("stone", "Decoration"),
        ("depot", "Depot"),
        ("container", "Containers"),
        ("chest", "Containers"),
        ("effect", "Effects"),
        ("mountain", "Mountains"),
        ("border", "Borders"),
        ("magicfield", "Effects"),
        ("field", "Effects"),
        ("house", "Houses"),
        ("shop", "Buildings"),
    ]
    for token, category in rules:
        if token in lowered:
            return category
    return fallback


class ItemDefinitionLoader:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> dict[int, OpenTibiaAsset]:
        if not self.path.exists():
            raise FileNotFoundError(f"missing file: {self.path}")
        root = _parse_xml(self.path)
        assets: dict[int, OpenTibiaAsset] = {}
        for element in root.findall("item"):
            raw_id = element.get("id")
            name = element.get("name") or element.get("article") or "unnamed item"
            if raw_id is None:
                continue
            try:
                item_id = int(raw_id)
            except ValueError:
                continue
            flags = []
            category = _category_from_name(name)
            for attr in element.findall("attribute"):
                key = attr.get("key")
                value = attr.get("value")
                if key and value:
                    flags.append(f"{key}={value}")
                    category = _category_from_name(value, category)
            assets[item_id] = OpenTibiaAsset(
                asset_id=item_id,
                client_id=item_id,
                name=name,
                category=category,
                brush="Raw Item Brush",
                tileset="Raw Items",
                source_file=str(self.path),
                flags=tuple(flags),
            )
        return assets


class BrushMaterialLoader:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def load(self) -> dict[str, OpenTibiaBrush]:
        if not self.root.exists():
            raise FileNotFoundError(f"missing file: {self.root}")
        brushes: dict[str, OpenTibiaBrush] = {}
        self.unsupported_sources: list[str] = []
        for path in sorted(self.root.glob("*.xml")):
            try:
                xml_root = _parse_xml(path)
            except ValueError as exc:
                self.unsupported_sources.append(str(exc))
                continue
            for element in xml_root.findall(".//brush"):
                name = element.get("name")
                if not name:
                    continue
                brush_type = element.get("type") or path.stem
                grammar = _brush_grammar(element, brush_type)
                item_ids = tuple(dict.fromkeys(_item_ids(element)))
                look_id = _int_or_none(element.get("lookid"))
                server_look_id = _int_or_none(element.get("server_lookid"))
                # lookid is a client appearance used by the palette. It must
                # never be merged into the server item catalog as an item ID.
                item_id = server_look_id or next(iter(item_ids), None)
                category = _category_from_name(name, _category_from_name(path.stem, "Raw Items"))
                brushes[name.lower()] = OpenTibiaBrush(
                    name=name,
                    brush_type=brush_type,
                    item_id=item_id,
                    category=category,
                    source_file=str(path),
                    flags=tuple(f"{key}={value}" for key, value in element.attrib.items() if key not in {"name", "type", "lookid"}),
                    item_ids=item_ids,
                    look_id=look_id,
                    server_look_id=server_look_id,
                    grammar=grammar,
                )
        return brushes


def _brush_grammar(element: ET.Element, brush_type: str) -> dict[str, object]:
    return {
        "version": 1,
        "type": brush_type,
        "attributes": _typed_attributes(element.attrib),
        "nodes": tuple(_element_record(child) for child in list(element)),
        "item_ids": tuple(dict.fromkeys(_item_ids(element))),
    }


def _element_record(element: ET.Element) -> dict[str, object]:
    return {
        "tag": element.tag.strip().lower().replace("-", "_"),
        "attributes": _typed_attributes(element.attrib),
        "children": tuple(_element_record(child) for child in list(element)),
    }


def _item_ids(element: ET.Element) -> list[int]:
    values: list[int] = []
    for child in element.iter():
        if child.tag.strip().lower() not in {"item", "door"}:
            continue
        item_id = _int_or_none(child.get("id"))
        if item_id is not None:
            values.append(item_id)
        start = _int_or_none(child.get("fromid"))
        end = _int_or_none(child.get("toid"))
        if start is not None and end is not None and start <= end:
            values.extend(range(start, end + 1))
    return values


def _typed_attributes(attributes: dict[str, str]) -> dict[str, object]:
    return {key: _typed_value(value) for key, value in attributes.items()}


def _typed_value(value: str) -> object:
    lowered = value.strip().lower()
    if lowered in {"true", "yes"}:
        return True
    if lowered in {"false", "no"}:
        return False
    parsed = _int_or_none(value)
    return parsed if parsed is not None else value


def _int_or_none(value: object) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None
