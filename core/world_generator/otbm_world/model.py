from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from core.editor import RMEEditorCore

LAYER_PRIORITY = {
    "ground": 0,
    "water": 10,
    "road": 20,
    "floor": 30,
    "wall": 40,
    "door": 50,
    "stair": 60,
}
SUPPORTED_ATTRIBUTE_KEYS = {
    "action_id",
    "depot_id",
    "house_door_id",
    "teleport_destination",
    "count",
    "charges",
    "description",
    "text",
    "tile_flags",
    "unique_id",
}


@dataclass(frozen=True)
class OtbmItem:
    item_id: int
    layer: str
    source_id: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    children: Tuple["OtbmItem", ...] = ()


@dataclass(frozen=True)
class OtbmTile:
    x: int
    y: int
    z: int
    items: Tuple[OtbmItem, ...]
    attributes: Dict[str, Any] = field(default_factory=dict)
    house_id: int | None = None


@dataclass(frozen=True)
class OtbmWorldModel:
    width: int
    height: int
    tiles: Tuple[OtbmTile, ...]
    metadata: Dict[str, Any]
    towns: Tuple[Dict[str, Any], ...] = ()
    waypoints: Tuple[Dict[str, Any], ...] = ()

    def to_json_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_world_model(certified_inputs: Mapping[str, Any]) -> OtbmWorldModel:
    tile_assembly = certified_inputs["CERTIFIED_TILE_ASSEMBLY_MODEL.json"]
    tiles_by_coord: Dict[Tuple[int, int, int], List[OtbmItem]] = {}
    for tile in _iter_physical_tiles(tile_assembly):
        coord = tile.get("coordinates") or {}
        x, y, z = int(coord["x"]), int(coord["y"]), int(coord["z"])
        item_id = int(tile["tile_id"])
        if item_id <= 0 or item_id > 0xFFFF:
            raise ValueError(f"invalid official tile/item id: {item_id}")
        layer = str(tile.get("layer") or "item")
        item = _item_from_mapping(tile, layer=layer)
        tiles_by_coord.setdefault((x, y, z), []).append(item)

    editor_core = RMEEditorCore(Path.cwd())
    for coord, items in sorted(tiles_by_coord.items()):
        declared_ground = next(
            (item.item_id for item in items if item.layer.lower() in {"ground", "water"}),
            None,
        )
        if declared_ground is None:
            editor_core.map.set_stack(coord, [item.item_id for item in items])
        else:
            editor_core.map.set_stack_exact(
                coord,
                declared_ground,
                [item.item_id for item in items if item.item_id != declared_ground],
            )
    postprocess_report = editor_core.postprocessor.run(tiles_by_coord.keys())
    for coord, source_items in sorted(tiles_by_coord.items()):
        declared_ground = next(
            (item.item_id for item in source_items if item.layer.lower() in {"ground", "water"}),
            None,
        )
        if declared_ground is None:
            continue
        processed = editor_core.map.get_tile(coord)
        processed_ids = processed.stack_ids() if processed else []
        source_ids = [item.item_id for item in source_items]
        generated = [item_id for item_id in processed_ids if item_id not in source_ids]
        objects = [item.item_id for item in source_items if item.item_id != declared_ground]
        editor_core.map.set_stack_exact(
            coord,
            declared_ground,
            editor_core.item_catalog.sort_items(objects + generated),
        )

    tiles: List[OtbmTile] = []
    max_x = max_y = 0
    for (x, y, z), editable_tile in sorted(editor_core.map.tiles.items()):
        ordered_items = tuple(
            _items_from_rme_stack(
                editable_tile.stack_ids(),
                list(tiles_by_coord.get((x, y, z), [])),
                editor_core,
                x,
                y,
                z,
            )
        )
        tiles.append(OtbmTile(x=x, y=y, z=z, items=ordered_items))
        max_x = max(max_x, x)
        max_y = max(max_y, y)

    metadata = dict(tile_assembly.get("metadata") or {})
    metadata.update(
        {
            "artifact": "OTBM_WORLD_MODEL",
            "compiler": "WGL-08",
            "serialization_only": True,
            "rme_editor_core_p0": {
                "enabled": True,
                "flow": [
                    "material_catalog",
                    "editable_map",
                    "brush_postprocess",
                    "otbm_roundtrip_validator",
                ],
                "item_catalog": editor_core.item_catalog.audit(),
                "material_catalog": editor_core.material_catalog.audit(),
                "postprocess": postprocess_report.to_dict(),
            },
            "source_artifacts": sorted(certified_inputs),
        }
    )
    return OtbmWorldModel(
        width=max_x + 1,
        height=max_y + 1,
        tiles=tuple(tiles),
        metadata=metadata,
    )


def _items_from_rme_stack(
    ordered_ids: Iterable[int],
    source_items: list[OtbmItem],
    editor_core: RMEEditorCore,
    x: int,
    y: int,
    z: int,
) -> Iterable[OtbmItem]:
    remaining = list(source_items)
    for index, item_id in enumerate(ordered_ids):
        match_index = next((i for i, item in enumerate(remaining) if item.item_id == item_id), None)
        if match_index is not None:
            yield remaining.pop(match_index)
            continue
        item_type = editor_core.item_catalog.get(item_id)
        yield OtbmItem(
            item_id=int(item_id),
            layer=_layer_from_item_type(item_type),
            source_id=f"rme_editor_core:{x}:{y}:{z}:{index}",
            attributes={},
        )


def _layer_from_item_type(item_type: Any) -> str:
    if item_type.is_ground:
        return "ground"
    if item_type.is_wall:
        return "wall"
    if item_type.is_door:
        return "door"
    if item_type.is_table or item_type.is_carpet or item_type.is_border:
        return "floor"
    return "item"


def _iter_physical_tiles(tile_assembly: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    for key in sorted(tile_assembly):
        value = tile_assembly[key]
        if not key.endswith("_tile_model") or not isinstance(value, Mapping):
            continue
        for tile in value.get("tiles") or []:
            if isinstance(tile, Mapping):
                yield tile


def _extract_attributes(tile: Mapping[str, Any]) -> Dict[str, Any]:
    attributes: Dict[str, Any] = {}
    nested = tile.get("attributes")
    if isinstance(nested, Mapping):
        for key, value in nested.items():
            if key in SUPPORTED_ATTRIBUTE_KEYS:
                attributes[key] = value
    for key in SUPPORTED_ATTRIBUTE_KEYS:
        if key in tile:
            attributes[key] = tile[key]
    return attributes


def _item_from_mapping(tile: Mapping[str, Any], *, layer: str = "item") -> OtbmItem:
    item_id = int(tile.get("tile_id", tile.get("item_id", 0)))
    if not 0 < item_id <= 0xFFFF:
        raise ValueError(f"invalid official tile/item id: {item_id}")
    children = tuple(
        _item_from_mapping(child, layer=str(child.get("layer") or "item"))
        for child in tile.get("children", ())
        if isinstance(child, Mapping)
    )
    return OtbmItem(
        item_id=item_id,
        layer=layer,
        source_id=str(tile.get("id") or tile.get("source_id") or ""),
        attributes=_extract_attributes(tile),
        children=children,
    )
