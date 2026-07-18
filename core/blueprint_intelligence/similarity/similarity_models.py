"""BI-4 dataset-backed similarity models."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SimilarityFeatureVector:
    """Normalized feature vector for a BI-3.5C blueprint record."""

    blueprint_id: str
    blueprint_type: str
    numeric_features: dict[str, float] = field(default_factory=dict)
    categorical_features: dict[str, str] = field(default_factory=dict)
    set_features: dict[str, list[str]] = field(default_factory=dict)
    bounds: dict[str, float | None] = field(default_factory=dict)
    position: dict[str, float | None] = field(default_factory=dict)
    provenance: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "blueprint_id": self.blueprint_id,
            "blueprint_type": self.blueprint_type,
            "numeric_features": _sorted_float_dict(self.numeric_features),
            "categorical_features": dict(sorted(self.categorical_features.items())),
            "set_features": {
                key: sorted(values) for key, values in sorted(self.set_features.items())
            },
            "bounds": dict(sorted(self.bounds.items())),
            "position": dict(sorted(self.position.items())),
            "provenance": dict(sorted(self.provenance.items())),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SimilarityFeatureVector:
        return cls(
            blueprint_id=str(data["blueprint_id"]),
            blueprint_type=str(data["blueprint_type"]),
            numeric_features={
                str(key): float(value) for key, value in data.get("numeric_features", {}).items()
            },
            categorical_features={
                str(key): str(value) for key, value in data.get("categorical_features", {}).items()
            },
            set_features={
                str(key): [str(item) for item in value]
                for key, value in data.get("set_features", {}).items()
            },
            bounds={
                str(key): (None if value is None else float(value))
                for key, value in data.get("bounds", {}).items()
            },
            position={
                str(key): (None if value is None else float(value))
                for key, value in data.get("position", {}).items()
            },
            provenance={str(key): str(value) for key, value in data.get("provenance", {}).items()},
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


@dataclass(slots=True)
class SimilarityScore:
    """Type-specific similarity score with dimensional breakdown."""

    score: float
    dimensions: dict[str, float]
    explanation: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 6),
            "dimensions": _sorted_float_dict(self.dimensions),
            "explanation": list(self.explanation),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SimilarityScore:
        return cls(
            score=float(data["score"]),
            dimensions={
                str(key): float(value) for key, value in data.get("dimensions", {}).items()
            },
            explanation=[str(item) for item in data.get("explanation", [])],
        )


@dataclass(slots=True)
class SimilarityMatch:
    """Ranked similarity match between two existing blueprints."""

    source_blueprint_id: str
    target_blueprint_id: str
    blueprint_type: str
    score: float
    rank: int
    explanation: list[str]
    provenance: dict[str, str]
    dimensions: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_blueprint_id": self.source_blueprint_id,
            "target_blueprint_id": self.target_blueprint_id,
            "blueprint_type": self.blueprint_type,
            "score": round(self.score, 6),
            "rank": self.rank,
            "explanation": list(self.explanation),
            "provenance": dict(sorted(self.provenance.items())),
            "dimensions": _sorted_float_dict(self.dimensions),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SimilarityMatch:
        return cls(
            source_blueprint_id=str(data["source_blueprint_id"]),
            target_blueprint_id=str(data["target_blueprint_id"]),
            blueprint_type=str(data["blueprint_type"]),
            score=float(data["score"]),
            rank=int(data["rank"]),
            explanation=[str(item) for item in data.get("explanation", [])],
            provenance={str(key): str(value) for key, value in data.get("provenance", {}).items()},
            dimensions={
                str(key): float(value) for key, value in data.get("dimensions", {}).items()
            },
        )


@dataclass(slots=True)
class SimilarityQuery:
    """Recommendation query over existing blueprint features."""

    blueprint_type: str
    numeric_features: dict[str, float] = field(default_factory=dict)
    categorical_features: dict[str, str] = field(default_factory=dict)
    set_features: dict[str, list[str]] = field(default_factory=dict)
    bounds: dict[str, float | None] = field(default_factory=dict)
    position: dict[str, float | None] = field(default_factory=dict)

    def to_feature_vector(self) -> SimilarityFeatureVector:
        return SimilarityFeatureVector(
            blueprint_id="query",
            blueprint_type=self.blueprint_type,
            numeric_features=dict(self.numeric_features),
            categorical_features=dict(self.categorical_features),
            set_features={key: list(value) for key, value in self.set_features.items()},
            bounds=dict(self.bounds),
            position=dict(self.position),
            provenance={"source": "query"},
        )


@dataclass(slots=True)
class SimilarityIndex:
    """Serializable BI-4 similarity index."""

    index_id: str
    source_dataset: str
    source_pattern_catalog: str
    generator_version: str
    blueprint_counts: dict[str, int]
    matches: dict[str, list[SimilarityMatch]]
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "index_id": self.index_id,
            "source_dataset": self.source_dataset,
            "source_pattern_catalog": self.source_pattern_catalog,
            "generator_version": self.generator_version,
            "blueprint_counts": dict(sorted(self.blueprint_counts.items())),
            "matches": {
                key: [match.to_dict() for match in value]
                for key, value in sorted(self.matches.items())
            },
            "provenance": self.provenance,
        }


def _sorted_float_dict(values: dict[str, float]) -> dict[str, float]:
    return {key: round(float(value), 6) for key, value in sorted(values.items())}


__all__ = [
    "SimilarityFeatureVector",
    "SimilarityIndex",
    "SimilarityMatch",
    "SimilarityQuery",
    "SimilarityScore",
]
