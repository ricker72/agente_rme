"""OTBM-compatible data to canonical BI-1 Blueprint extractor."""

from __future__ import annotations

import importlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from core.blueprint_intelligence.extractors.base_extractor import BaseBlueprintExtractor
from core.blueprint_intelligence.extractors.extractor_errors import (
    BlueprintExtractionError,
    InvalidOTBMBlueprintError,
    UnsupportedBlueprintSourceError,
)
from core.blueprint_intelligence.models.blueprint import Blueprint
from core.blueprint_intelligence.models.provenance import Provenance

TYPE_MAPPING = {
    "city": "city",
    "hunt": "hunt",
    "dungeon": "dungeon",
    "boss": "boss_area",
    "boss_room": "boss_area",
    "boss_area": "boss_area",
    "quest": "quest_chain",
    "quest_chain": "quest_chain",
    "region": "region",
    "biome": "region",
    "area": "region",
}


class OTBMBlueprintExtractor(BaseBlueprintExtractor):
    """Extract BI-1 Blueprints from real OTBM files or explicit JSON fixtures."""

    def __init__(self, allow_json_fixtures: bool = False) -> None:
        self.allow_json_fixtures = allow_json_fixtures

    def supports(self, source: str | Path) -> bool:
        suffix = Path(source).suffix.lower()
        return suffix == ".otbm" or (suffix == ".json" and self.allow_json_fixtures)

    def extract(self, source: str | Path) -> list[Blueprint]:
        path = Path(source)
        suffix = path.suffix.lower()
        if suffix == ".json" and not self.allow_json_fixtures:
            raise UnsupportedBlueprintSourceError(
                "JSON OTBM fixtures require allow_json_fixtures=True."
            )
        if not self.supports(path):
            raise UnsupportedBlueprintSourceError(
                f"Unsupported blueprint source '{path}'; OTBM extractor supports .otbm files"
                " and explicit .json fixtures only."
            )
        if not path.exists():
            raise BlueprintExtractionError(f"OTBM Blueprint source file does not exist: {path}")

        if suffix == ".json":
            return [self._extract_fixture(path)]
        return [self._extract_otbm(path)]

    def _extract_fixture(self, path: Path) -> Blueprint:
        try:
            raw_data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise InvalidOTBMBlueprintError(
                f"Invalid OTBM fixture JSON in '{path}': {exc.msg}"
            ) from exc
        if not isinstance(raw_data, dict):
            raise InvalidOTBMBlueprintError("OTBM fixture must be a JSON object.")
        return _blueprint_from_fixture(raw_data, path)

    def _extract_otbm(self, path: Path) -> Blueprint:
        importer_class = _load_otbm_importer()
        try:
            result = importer_class().import_file(path)
        except Exception as exc:
            raise BlueprintExtractionError(
                f"OTBM importer failed while reading '{path}': {exc}"
            ) from exc
        if not isinstance(result, dict) or not result.get("success"):
            error = result.get("error", "unknown importer failure") if isinstance(result, dict) else result
            raise BlueprintExtractionError(f"OTBM importer could not load '{path}': {error}")
        return _blueprint_from_import_result(result, path)


def _load_otbm_importer() -> type[Any]:
    try:
        module = importlib.import_module("core.otbm.otbm_importer")
        importer_class = cast(type[Any], getattr(module, "OTBMImporter"))
    except Exception as exc:
        raise BlueprintExtractionError(
            "OTBM importer is unavailable; cannot extract Blueprint data from real .otbm files."
        ) from exc
    return importer_class


def _blueprint_from_fixture(fixture: dict[str, Any], path: Path) -> Blueprint:
    source_type = _text_field(fixture, "type") or "unknown"
    name = _text_field(fixture, "name")
    blueprint_id = _text_field(fixture, "id") or _slug_from_name_type(name, source_type)
    name = name or blueprint_id
    metadata = fixture.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        raise InvalidOTBMBlueprintError("OTBM fixture metadata must be an object.")

    try:
        return Blueprint(
            blueprint_id=blueprint_id,
            name=name,
            blueprint_type=_map_type(source_type),
            width=_required_positive_int(fixture, "width"),
            height=_required_positive_int(fixture, "height"),
            regions=_required_string_list(fixture, "regions"),
            patterns=[],
            constraints=[],
            provenance=Provenance(
                source=_metadata_source(metadata) or str(path),
                dataset="otbm",
                generator_version="2.0",
                seed=0,
                timestamp=_utc_timestamp(),
            ),
        )
    except (TypeError, ValueError) as exc:
        raise InvalidOTBMBlueprintError(f"Invalid OTBM fixture in '{path}': {exc}") from exc


def _blueprint_from_import_result(result: dict[str, Any], path: Path) -> Blueprint:
    map_info = result.get("map_info")
    stats = result.get("stats")
    world_dict = result.get("world_dict")
    map_info = map_info if isinstance(map_info, dict) else {}
    stats = stats if isinstance(stats, dict) else {}
    world_dict = world_dict if isinstance(world_dict, dict) else {}
    width = _positive_int_value(map_info.get("width")) or _positive_int_value(world_dict.get("width")) or 1
    height = (
        _positive_int_value(map_info.get("height")) or _positive_int_value(world_dict.get("height")) or 1
    )
    regions = _regions_from_world(world_dict)
    if not regions and _positive_int_value(stats.get("cities")):
        regions = ["cities"]
    return Blueprint(
        blueprint_id=_slug_from_name_type(path.stem, "region"),
        name=path.stem,
        blueprint_type="region",
        width=width,
        height=height,
        regions=regions,
        patterns=[],
        constraints=[],
        provenance=Provenance(
            source=str(path),
            dataset="otbm",
            generator_version="2.0",
            seed=0,
            timestamp=_utc_timestamp(),
        ),
    )


def _map_type(source_type: str) -> str:
    return TYPE_MAPPING.get(source_type.strip().lower(), "region")


def _text_field(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if isinstance(value, str) and value:
        return value
    return None


def _required_positive_int(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    raise InvalidOTBMBlueprintError(f"OTBM fixture field '{key}' must be a positive int.")


def _positive_int_value(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return None


def _required_string_list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key)
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value)
    raise InvalidOTBMBlueprintError(f"OTBM fixture field '{key}' must be a list[str].")


def _metadata_source(metadata: object) -> str | None:
    if not isinstance(metadata, dict):
        return None
    value = metadata.get("source")
    if isinstance(value, str) and value:
        return value
    return None


def _regions_from_world(world_dict: dict[str, Any]) -> list[str]:
    cities = world_dict.get("cities")
    if not isinstance(cities, list):
        return []
    names: list[str] = []
    for city in cities:
        if isinstance(city, dict):
            name = city.get("name")
            if isinstance(name, str) and name:
                names.append(name)
    return names


def _slug_from_name_type(name: str | None, source_type: str) -> str:
    source = name or source_type or "otbm_blueprint"
    slug = re.sub(r"[^a-z0-9]+", "_", source.lower()).strip("_")
    return slug or "otbm_blueprint"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()
