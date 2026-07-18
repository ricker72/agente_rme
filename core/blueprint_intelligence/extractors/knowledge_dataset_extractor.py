"""Knowledge Dataset JSON to canonical BI-1 Blueprint extractor."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.blueprint_intelligence.extractors.base_extractor import BaseBlueprintExtractor
from core.blueprint_intelligence.extractors.extractor_errors import (
    BlueprintExtractionError,
    InvalidKnowledgeDatasetError,
    UnsupportedBlueprintSourceError,
)
from core.blueprint_intelligence.models.blueprint import Blueprint
from core.blueprint_intelligence.models.provenance import Provenance

ROOT_KEYS = ("entries", "items", "records", "knowledge_entries")
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


class KnowledgeDatasetExtractor(BaseBlueprintExtractor):
    """Extract canonical Blueprint objects from Knowledge Dataset JSON files."""

    def supports(self, source: str | Path) -> bool:
        return Path(source).suffix.lower() == ".json"

    def extract(self, source: str | Path) -> list[Blueprint]:
        path = Path(source)
        if not self.supports(path):
            raise UnsupportedBlueprintSourceError(
                f"Unsupported blueprint source '{path}'; Knowledge Dataset extractor supports .json files only."
            )
        if not path.exists():
            raise BlueprintExtractionError(f"Knowledge Dataset source file does not exist: {path}")

        try:
            raw_data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise InvalidKnowledgeDatasetError(
                f"Invalid Knowledge Dataset JSON in '{path}': {exc.msg}"
            ) from exc

        entries = _coerce_entries(raw_data)
        return [
            blueprint
            for entry in entries
            if isinstance(entry, dict)
            for blueprint in [_entry_to_blueprint(entry, path.name)]
            if blueprint is not None
        ]


def _coerce_entries(raw_data: Any) -> list[Any]:
    if isinstance(raw_data, list):
        return raw_data
    if isinstance(raw_data, dict):
        for key in ROOT_KEYS:
            value = raw_data.get(key)
            if isinstance(value, list):
                return value
        if raw_data:
            return [raw_data]
    return []


def _entry_to_blueprint(entry: dict[str, Any], dataset_name: str) -> Blueprint | None:
    source_type = _entry_type(entry)
    blueprint_type = TYPE_MAPPING.get(source_type)
    if blueprint_type is None:
        return None

    name = _text_field(entry, "name") or _text_field(entry, "title")
    blueprint_id = (
        _text_field(entry, "id")
        or _text_field(entry, "blueprint_id")
        or _slug_from_name_type(name, source_type)
    )
    name = name or blueprint_id

    return Blueprint(
        blueprint_id=blueprint_id,
        name=name,
        blueprint_type=blueprint_type,
        width=_positive_int_field(entry, "width"),
        height=_positive_int_field(entry, "height"),
        regions=_string_list_field(entry, "regions") or _string_list_field(entry, "areas"),
        patterns=[],
        constraints=[],
        provenance=Provenance(
            source=_text_field(entry, "source") or "knowledge_dataset",
            dataset=dataset_name,
            generator_version="2.0",
            seed=0,
            timestamp=_text_field(entry, "timestamp") or _utc_timestamp(),
        ),
    )


def _entry_type(entry: dict[str, Any]) -> str:
    for key in ("type", "entry_type", "blueprint_type", "category"):
        value = entry.get(key)
        if isinstance(value, str):
            return value.strip().lower()
    return ""


def _text_field(entry: dict[str, Any], key: str) -> str | None:
    value = entry.get(key)
    if isinstance(value, str) and value:
        return value
    return None


def _positive_int_field(entry: dict[str, Any], key: str) -> int:
    value = entry.get(key)
    if value is None:
        metadata = entry.get("metadata")
        if isinstance(metadata, dict):
            value = metadata.get(key)
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return 1


def _string_list_field(entry: dict[str, Any], key: str) -> list[str]:
    value = entry.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _slug_from_name_type(name: str | None, source_type: str) -> str:
    source = name or source_type or "blueprint"
    slug = re.sub(r"[^a-z0-9]+", "_", source.lower()).strip("_")
    return slug or "blueprint"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()
