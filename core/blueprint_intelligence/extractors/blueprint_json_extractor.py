"""Explicit Blueprint JSON to canonical BI-1 Blueprint extractor."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from core.blueprint_intelligence.extractors.base_extractor import BaseBlueprintExtractor
from core.blueprint_intelligence.extractors.extractor_errors import (
    BlueprintExtractionError,
    InvalidBlueprintJsonError,
    UnsupportedBlueprintSourceError,
)
from core.blueprint_intelligence.models.blueprint import Blueprint


class BlueprintJsonExtractor(BaseBlueprintExtractor):
    """Extract already-structured Blueprint JSON into BI-1 Blueprint objects."""

    def supports(self, source: str | Path) -> bool:
        return Path(source).suffix.lower() == ".json"

    def extract(self, source: str | Path) -> list[Blueprint]:
        path = Path(source)
        if not self.supports(path):
            raise UnsupportedBlueprintSourceError(
                f"Unsupported blueprint source '{path}'; Blueprint JSON extractor supports .json files only."
            )
        if not path.exists():
            raise BlueprintExtractionError(f"Blueprint JSON source file does not exist: {path}")

        try:
            raw_data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise InvalidBlueprintJsonError(
                f"Invalid Blueprint JSON in '{path}': {exc.msg}"
            ) from exc

        blueprint_data = _coerce_blueprint_data(raw_data)
        blueprints: list[Blueprint] = []
        for item in blueprint_data:
            try:
                blueprints.append(Blueprint.from_dict(item))
            except (KeyError, TypeError, ValueError) as exc:
                raise InvalidBlueprintJsonError(
                    f"Invalid Blueprint object in '{path}': {exc}"
                ) from exc
        return blueprints


def _coerce_blueprint_data(raw_data: Any) -> list[dict[str, Any]]:
    if isinstance(raw_data, list):
        return _require_object_list(raw_data)
    if isinstance(raw_data, dict):
        blueprint = raw_data.get("blueprint")
        if blueprint is not None:
            if not isinstance(blueprint, dict):
                raise InvalidBlueprintJsonError("Root 'blueprint' must be a Blueprint object.")
            return [cast(dict[str, Any], blueprint)]

        blueprints = raw_data.get("blueprints")
        if blueprints is not None:
            if not isinstance(blueprints, list):
                raise InvalidBlueprintJsonError("Root 'blueprints' must be a list.")
            return _require_object_list(blueprints)

        if _looks_like_blueprint(raw_data):
            return [cast(dict[str, Any], raw_data)]

    raise InvalidBlueprintJsonError("Unsupported Blueprint JSON shape.")


def _require_object_list(items: list[Any]) -> list[dict[str, Any]]:
    if not all(isinstance(item, dict) for item in items):
        raise InvalidBlueprintJsonError("Blueprint JSON lists must contain only Blueprint objects.")
    return [cast(dict[str, Any], item) for item in items]


def _looks_like_blueprint(item: dict[str, Any]) -> bool:
    required_keys = {
        "blueprint_id",
        "name",
        "blueprint_type",
        "width",
        "height",
        "regions",
        "patterns",
        "constraints",
        "provenance",
    }
    return required_keys.issubset(item.keys())
