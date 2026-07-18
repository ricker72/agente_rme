"""Feature extraction for BI-4 dataset-backed similarity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .similarity_models import SimilarityFeatureVector


class SimilarityFeatureExtractor:
    """Extract deterministic feature vectors from Blueprint Dataset V1."""

    def __init__(self, pattern_catalog: dict[str, Any] | None = None) -> None:
        self.pattern_catalog = pattern_catalog or {}
        self._spawn_pattern_species = {
            pattern.get("name", "")
            for pattern in self.pattern_catalog.get("spawn_patterns", [])
            if isinstance(pattern, dict)
        }

    def extract_dataset(self, dataset: dict[str, Any]) -> dict[str, SimilarityFeatureVector]:
        vectors = {}
        blueprints = dataset.get("blueprints", {})
        for key in ("cities", "hunts", "spawns", "dungeons"):
            for blueprint in blueprints.get(key, []):
                vector = self.extract_blueprint(blueprint)
                vectors[vector.blueprint_id] = vector
        return dict(sorted(vectors.items()))

    def extract_blueprint(self, blueprint: dict[str, Any]) -> SimilarityFeatureVector:
        blueprint_type = str(blueprint["type"])
        if blueprint_type == "city":
            return self._city_vector(blueprint)
        if blueprint_type == "hunt":
            return self._hunt_vector(blueprint)
        if blueprint_type == "spawn":
            return self._spawn_vector(blueprint)
        if blueprint_type == "dungeon":
            return self._dungeon_vector(blueprint)
        raise ValueError(f"Unsupported blueprint type: {blueprint_type}")

    def _city_vector(self, blueprint: dict[str, Any]) -> SimilarityFeatureVector:
        bounds = _numeric_bounds(blueprint.get("estimated_bounds", {}))
        complete = 1.0 if blueprint.get("temple_position") is not None else 0.5
        return SimilarityFeatureVector(
            blueprint_id=str(blueprint["blueprint_id"]),
            blueprint_type="city",
            numeric_features={
                "house_count": float(blueprint.get("house_count", 0)),
                "metadata_completeness": complete,
                "town_id": float(blueprint.get("town_id", 0)),
            },
            categorical_features={
                "status": str(blueprint.get("status", "")),
                "type": "city",
            },
            bounds=bounds,
            provenance=_string_provenance(blueprint),
        )

    def _hunt_vector(self, blueprint: dict[str, Any]) -> SimilarityFeatureVector:
        bounds = _numeric_bounds(blueprint.get("estimated_bounds", {}))
        return SimilarityFeatureVector(
            blueprint_id=str(blueprint["blueprint_id"]),
            blueprint_type="hunt",
            numeric_features={
                "spawn_count": float(blueprint.get("spawn_count", 0)),
                "density_score": float(blueprint.get("density_score", 0.0)),
                "z_level": _z_center(bounds),
            },
            set_features={
                "monster_species": [str(item) for item in blueprint.get("monster_species", [])]
            },
            bounds=bounds,
            provenance=_string_provenance(blueprint),
        )

    def _spawn_vector(self, blueprint: dict[str, Any]) -> SimilarityFeatureVector:
        monster_name = str(blueprint.get("monster_name", ""))
        return SimilarityFeatureVector(
            blueprint_id=str(blueprint["blueprint_id"]),
            blueprint_type="spawn",
            numeric_features={
                "radius": float(blueprint.get("radius", 0)),
                "spawn_time": float(blueprint.get("spawn_time", 0)),
                "catalog_species_known": (
                    1.0 if monster_name in self._spawn_pattern_species else 0.0
                ),
            },
            categorical_features={
                "monster_name": monster_name,
                "density_group": str(blueprint.get("density_group", "")),
            },
            position=_numeric_position(blueprint.get("position", {})),
            provenance=_string_provenance(blueprint),
        )

    def _dungeon_vector(self, blueprint: dict[str, Any]) -> SimilarityFeatureVector:
        bounds = _numeric_bounds(blueprint.get("estimated_bounds", {}))
        return SimilarityFeatureVector(
            blueprint_id=str(blueprint["blueprint_id"]),
            blueprint_type="dungeon",
            numeric_features={
                "spawn_count": float(blueprint.get("spawn_count", 0)),
                "density": _density_from_bounds(blueprint.get("spawn_count", 0), bounds),
                "z_level": _z_center(bounds),
            },
            set_features={
                "monster_species": [str(item) for item in blueprint.get("monster_species", [])]
            },
            bounds=bounds,
            provenance=_string_provenance(blueprint),
        )


def load_dataset_features(
    dataset_path: str | Path,
    pattern_catalog_path: str | Path | None = None,
) -> dict[str, SimilarityFeatureVector]:
    dataset = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    pattern_catalog = None
    if pattern_catalog_path is not None and Path(pattern_catalog_path).exists():
        pattern_catalog = json.loads(Path(pattern_catalog_path).read_text(encoding="utf-8"))
    return SimilarityFeatureExtractor(pattern_catalog).extract_dataset(dataset)


def _numeric_bounds(raw: dict[str, Any]) -> dict[str, float | None]:
    return {
        key: (None if raw.get(key) is None else float(raw[key]))
        for key in ("min_x", "min_y", "min_z", "max_x", "max_y", "max_z")
    }


def _numeric_position(raw: dict[str, Any]) -> dict[str, float | None]:
    return {key: (None if raw.get(key) is None else float(raw[key])) for key in ("x", "y", "z")}


def _z_center(bounds: dict[str, float | None]) -> float:
    min_z = bounds.get("min_z")
    max_z = bounds.get("max_z")
    if min_z is None or max_z is None:
        return 0.0
    return (min_z + max_z) / 2.0


def _density_from_bounds(spawn_count: object, bounds: dict[str, float | None]) -> float:
    min_x = bounds.get("min_x")
    max_x = bounds.get("max_x")
    min_y = bounds.get("min_y")
    max_y = bounds.get("max_y")
    if min_x is None or max_x is None or min_y is None or max_y is None:
        return 0.0
    area = max((max_x - min_x + 1.0) * (max_y - min_y + 1.0), 1.0)
    if not isinstance(spawn_count, (int, float)) or isinstance(spawn_count, bool):
        return 0.0
    return float(spawn_count) / area


def _string_provenance(blueprint: dict[str, Any]) -> dict[str, str]:
    raw = blueprint.get("provenance", {})
    if not isinstance(raw, dict):
        return {}
    return {str(key): str(value) for key, value in raw.items() if value is not None}


__all__ = ["SimilarityFeatureExtractor", "load_dataset_features"]
