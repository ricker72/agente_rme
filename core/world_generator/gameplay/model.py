from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping


def build_world_semantics_model(inputs: Mapping[str, Any]) -> Dict[str, Any]:
    blueprint = inputs["CERTIFIED_BLUEPRINT.json"]
    otbm = inputs["CERTIFIED_OTBM_WORLD.json"]
    assembly = inputs["CERTIFIED_TILE_ASSEMBLY_MODEL.json"]
    tiles = list(_iter_tiles(assembly))
    return {
        "artifact": "WORLD_SEMANTICS_MODEL",
        "logical_only": True,
        "geometry_frozen": True,
        "source_world_id": (blueprint.get("metadata") or {}).get("world_id"),
        "source_seed": (blueprint.get("metadata") or {}).get("seed"),
        "otbm_fingerprint": otbm.get("fingerprint"),
        "semantic_sources": {
            "cities": sorted(item["id"] for item in blueprint.get("cities", [])),
            "villages": sorted(item["id"] for item in blueprint.get("villages", [])),
            "regions": sorted(item["id"] for item in blueprint.get("regions", [])),
            "dungeons": sorted(item["id"] for item in blueprint.get("dungeons", [])),
        },
        "tile_extent": _tile_extent(tiles),
        "tile_counts_by_layer": _counts_by_layer(tiles),
    }


def _iter_tiles(assembly: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    for key in sorted(assembly):
        value = assembly[key]
        if key.endswith("_tile_model") and isinstance(value, Mapping):
            for tile in value.get("tiles") or []:
                if isinstance(tile, Mapping):
                    yield tile


def _tile_extent(tiles: list[Mapping[str, Any]]) -> Dict[str, int]:
    coords = [tile["coordinates"] for tile in tiles if "coordinates" in tile]
    return {
        "min_x": min((int(c["x"]) for c in coords), default=0),
        "max_x": max((int(c["x"]) for c in coords), default=0),
        "min_y": min((int(c["y"]) for c in coords), default=0),
        "max_y": max((int(c["y"]) for c in coords), default=0),
        "min_z": min((int(c["z"]) for c in coords), default=0),
        "max_z": max((int(c["z"]) for c in coords), default=0),
    }


def _counts_by_layer(tiles: list[Mapping[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for tile in tiles:
        layer = str(tile.get("layer") or "unknown")
        counts[layer] = counts.get(layer, 0) + 1
    return dict(sorted(counts.items()))
