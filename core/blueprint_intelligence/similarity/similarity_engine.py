"""BI-4 Similarity Engine orchestrator."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .blueprint_similarity_engine import BlueprintSimilarityEngine
from .explanation_engine import explain_dimensions
from .feature_extractor import SimilarityFeatureExtractor
from .pattern_similarity_engine import PatternSimilarityEngine
from .similarity_metrics import (
    bounds_similarity,
    categorical_similarity,
    numeric_similarity,
    position_similarity,
    set_similarity,
    weighted_similarity,
)
from .similarity_models import (
    SimilarityFeatureVector,
    SimilarityIndex,
    SimilarityMatch,
    SimilarityQuery,
    SimilarityScore,
)
from .similarity_result import SimilarityResult

if TYPE_CHECKING:
    from ..models.blueprint import Blueprint
    from ..models.pattern import Pattern

GENERATOR_VERSION = "BI-4"
INDEX_ID = "similarity_index_v1"
DEFAULT_DATASET_PATH = Path("roadmap/v1.1/BLUEPRINT_DATASET_V1.json")
DEFAULT_PATTERN_CATALOG_PATH = Path("roadmap/v1.1/WORLD_PATTERN_CATALOG.json")
DEFAULT_INDEX_PATH = Path("roadmap/v1.1/SIMILARITY_INDEX.json")
DEFAULT_STABLE_INDEX_PATH = Path("datasets/blueprint_datasets/similarity_index_v1.json")


class SimilarityEngine:
    """Unified similarity engine with legacy and BI-4 dataset-backed APIs."""

    def __init__(self) -> None:
        self.blueprint_engine = BlueprintSimilarityEngine()
        self.pattern_engine = PatternSimilarityEngine()
        self.features: dict[str, SimilarityFeatureVector] = {}
        self.index: SimilarityIndex | None = None

    def compare_blueprints(self, target: Blueprint, candidate: Blueprint) -> SimilarityResult:
        """Compare two canonical BI-1 blueprints with the legacy engine."""
        return self.blueprint_engine.compare(target, candidate)

    def rank_blueprints(
        self, target: Blueprint, candidates: list[Blueprint]
    ) -> list[SimilarityResult]:
        """Rank canonical BI-1 blueprints with the legacy engine."""
        return self.blueprint_engine.rank(target, candidates)

    def compare_patterns(self, target: Pattern, candidate: Pattern) -> SimilarityResult:
        """Compare two canonical BI-1 patterns with the legacy engine."""
        return self.pattern_engine.compare(target, candidate)

    def rank_patterns(self, target: Pattern, candidates: list[Pattern]) -> list[SimilarityResult]:
        """Rank canonical BI-1 patterns with the legacy engine."""
        return self.pattern_engine.rank(target, candidates)

    def recommend_patterns(
        self, target: Blueprint, patterns: list[Pattern], limit: int = 10
    ) -> list[SimilarityResult]:
        """Recommend patterns for a canonical BI-1 blueprint target."""
        results = []
        for pattern in patterns:
            score = self._calculate_pattern_recommendation_score(target, pattern)
            reasons = self._get_pattern_recommendation_reasons(target, pattern)
            results.append(
                SimilarityResult(
                    target_id=target.blueprint_id,
                    candidate_id=pattern.pattern_id,
                    score=score,
                    category="pattern_recommendation",
                    source="similarity_engine",
                    reasons=reasons,
                )
            )
        results.sort(key=lambda item: (-item.score, item.candidate_id))
        return results[:limit]

    def build_index(
        self,
        dataset: dict[str, Any],
        pattern_catalog: dict[str, Any] | None = None,
        source_dataset: str = "BLUEPRINT_DATASET_V1.json",
        source_pattern_catalog: str = "WORLD_PATTERN_CATALOG.json",
    ) -> SimilarityIndex:
        """Build a deterministic similarity index from Blueprint Dataset V1."""
        self.features = SimilarityFeatureExtractor(pattern_catalog).extract_dataset(dataset)
        by_type = self._features_by_type()
        matches = {
            "cities": self._top_matches_for_type(by_type["city"], top_k=10),
            "hunts": self._top_matches_for_type(by_type["hunt"], top_k=10),
            "spawns": self._top_matches_for_type(by_type["spawn"], top_k=5),
            "dungeons": self._top_matches_for_type(by_type["dungeon"], top_k=10),
        }
        self.index = SimilarityIndex(
            index_id=INDEX_ID,
            source_dataset=source_dataset,
            source_pattern_catalog=source_pattern_catalog,
            generator_version=GENERATOR_VERSION,
            blueprint_counts={
                "cities": len(by_type["city"]),
                "hunts": len(by_type["hunt"]),
                "spawns": len(by_type["spawn"]),
                "dungeons": len(by_type["dungeon"]),
            },
            matches=matches,
            provenance={
                "strategy": "deterministic grouped top-k retrieval",
                "spawn_strategy": "grouped by monster species with nearby-position candidate windows",
                "hunt_strategy": "grouped by z-level and overlapping monster composition",
                "score_range": "0.0..100.0",
                "generator_version": GENERATOR_VERSION,
            },
        )
        return self.index

    def compare(self, source_id: str, target_id: str) -> SimilarityScore:
        """Compare two indexed feature vectors of the same blueprint type."""
        source = self._get_feature(source_id)
        target = self._get_feature(target_id)
        if source.blueprint_type != target.blueprint_type:
            raise ValueError("BI-4 compare requires matching blueprint types")
        return self._score(source, target)

    def find_similar(self, blueprint_id: str, top_k: int = 10) -> list[SimilarityMatch]:
        """Return top-k same-type matches for an indexed blueprint id."""
        source = self._get_feature(blueprint_id)
        candidates = [
            feature
            for feature in self._candidate_pool(source)
            if feature.blueprint_id != blueprint_id
        ]
        return self._rank_matches(source, candidates, top_k)

    def recommend_blueprints(
        self,
        query: SimilarityQuery | SimilarityFeatureVector,
        blueprint_type: str,
        top_k: int = 10,
    ) -> list[SimilarityMatch]:
        """Recommend existing blueprints for a query feature vector."""
        query_vector = query.to_feature_vector() if isinstance(query, SimilarityQuery) else query
        query_vector.blueprint_type = blueprint_type
        candidates = [
            feature
            for feature in self.features.values()
            if feature.blueprint_type == blueprint_type
        ]
        return self._rank_matches(query_vector, candidates, top_k)

    def export_index(self, path: str | Path) -> None:
        """Write the current similarity index to JSON."""
        if self.index is None:
            raise ValueError("No index has been built")
        _write_json(Path(path), self.index.to_dict())

    def load_index(self, path: str | Path) -> SimilarityIndex:
        """Load a similarity index JSON file."""
        data = _read_json(Path(path))
        matches = {
            key: [SimilarityMatch.from_dict(match) for match in value]
            for key, value in data.get("matches", {}).items()
        }
        self.index = SimilarityIndex(
            index_id=str(data["index_id"]),
            source_dataset=str(data["source_dataset"]),
            source_pattern_catalog=str(data["source_pattern_catalog"]),
            generator_version=str(data["generator_version"]),
            blueprint_counts={
                str(key): int(value) for key, value in data.get("blueprint_counts", {}).items()
            },
            matches=matches,
            provenance=data.get("provenance", {}),
        )
        return self.index

    def _score(
        self, source: SimilarityFeatureVector, target: SimilarityFeatureVector
    ) -> SimilarityScore:
        if source.blueprint_type == "city":
            dimensions = self._city_dimensions(source, target)
            weights = {
                "house_count": 0.30,
                "bounds": 0.25,
                "metadata": 0.25,
                "town_metadata": 0.20,
            }
        elif source.blueprint_type == "hunt":
            dimensions = self._hunt_dimensions(source, target)
            weights = {
                "monster_species": 0.35,
                "spawn_count": 0.25,
                "density_score": 0.25,
                "bounds": 0.15,
            }
        elif source.blueprint_type == "spawn":
            dimensions = self._spawn_dimensions(source, target)
            weights = {
                "monster_name": 0.45,
                "radius": 0.20,
                "spawn_time": 0.20,
                "position": 0.15,
            }
        elif source.blueprint_type == "dungeon":
            dimensions = self._dungeon_dimensions(source, target)
            weights = {
                "z_level": 0.25,
                "monster_species": 0.35,
                "density_score": 0.25,
                "bounds": 0.15,
            }
        else:
            raise ValueError(f"Unsupported blueprint type: {source.blueprint_type}")
        score = weighted_similarity(dimensions, weights)
        return SimilarityScore(
            score=score,
            dimensions=dimensions,
            explanation=explain_dimensions(dimensions),
        )

    def _city_dimensions(
        self, source: SimilarityFeatureVector, target: SimilarityFeatureVector
    ) -> dict[str, float]:
        return {
            "house_count": numeric_similarity(
                source.numeric_features.get("house_count"),
                target.numeric_features.get("house_count"),
            ),
            "bounds": bounds_similarity(source.bounds, target.bounds),
            "metadata": numeric_similarity(
                source.numeric_features.get("metadata_completeness"),
                target.numeric_features.get("metadata_completeness"),
            ),
            "town_metadata": max(
                categorical_similarity(
                    source.categorical_features.get("status"),
                    target.categorical_features.get("status"),
                ),
                numeric_similarity(
                    source.numeric_features.get("town_id"),
                    target.numeric_features.get("town_id"),
                ),
            ),
        }

    def _hunt_dimensions(
        self, source: SimilarityFeatureVector, target: SimilarityFeatureVector
    ) -> dict[str, float]:
        return {
            "monster_species": set_similarity(
                source.set_features.get("monster_species"),
                target.set_features.get("monster_species"),
            ),
            "spawn_count": numeric_similarity(
                source.numeric_features.get("spawn_count"),
                target.numeric_features.get("spawn_count"),
            ),
            "density_score": numeric_similarity(
                source.numeric_features.get("density_score"),
                target.numeric_features.get("density_score"),
            ),
            "bounds": bounds_similarity(source.bounds, target.bounds),
        }

    def _spawn_dimensions(
        self, source: SimilarityFeatureVector, target: SimilarityFeatureVector
    ) -> dict[str, float]:
        return {
            "monster_name": categorical_similarity(
                source.categorical_features.get("monster_name"),
                target.categorical_features.get("monster_name"),
            ),
            "radius": numeric_similarity(
                source.numeric_features.get("radius"),
                target.numeric_features.get("radius"),
            ),
            "spawn_time": numeric_similarity(
                source.numeric_features.get("spawn_time"),
                target.numeric_features.get("spawn_time"),
            ),
            "position": position_similarity(source.position, target.position),
        }

    def _dungeon_dimensions(
        self, source: SimilarityFeatureVector, target: SimilarityFeatureVector
    ) -> dict[str, float]:
        return {
            "z_level": numeric_similarity(
                source.numeric_features.get("z_level"),
                target.numeric_features.get("z_level"),
            ),
            "monster_species": set_similarity(
                source.set_features.get("monster_species"),
                target.set_features.get("monster_species"),
            ),
            "density_score": numeric_similarity(
                source.numeric_features.get("density"),
                target.numeric_features.get("density"),
            ),
            "bounds": bounds_similarity(source.bounds, target.bounds),
        }

    def _top_matches_for_type(
        self, features: list[SimilarityFeatureVector], top_k: int
    ) -> list[SimilarityMatch]:
        if features and features[0].blueprint_type == "spawn":
            return self._top_spawn_matches(features, top_k)
        if features and features[0].blueprint_type == "hunt":
            return self._top_hunt_matches(features, top_k)
        all_matches = []
        for source in sorted(features, key=lambda item: item.blueprint_id):
            all_matches.extend(self._rank_matches(source, self._candidate_pool(source), top_k))
        return all_matches

    def _top_spawn_matches(
        self, features: list[SimilarityFeatureVector], top_k: int
    ) -> list[SimilarityMatch]:
        by_species: dict[str, list[SimilarityFeatureVector]] = defaultdict(list)
        for feature in features:
            by_species[feature.categorical_features.get("monster_name", "")].append(feature)

        all_matches = []
        for species in sorted(by_species):
            species_features = sorted(
                by_species[species], key=lambda item: (_position_key(item), item.blueprint_id)
            )
            for index, source in enumerate(species_features):
                start = max(0, index - 25)
                end = min(len(species_features), index + 26)
                candidates = species_features[start:end]
                all_matches.extend(self._rank_matches(source, candidates, top_k))
        return all_matches

    def _top_hunt_matches(
        self, features: list[SimilarityFeatureVector], top_k: int
    ) -> list[SimilarityMatch]:
        by_group: dict[tuple[float, str], list[SimilarityFeatureVector]] = defaultdict(list)
        by_z: dict[float, list[SimilarityFeatureVector]] = defaultdict(list)
        for feature in features:
            z_level = feature.numeric_features.get("z_level", 0.0)
            primary_species = _primary_species(feature)
            by_group[(z_level, primary_species)].append(feature)
            by_z[z_level].append(feature)

        all_matches = []
        for source in sorted(features, key=lambda item: item.blueprint_id):
            z_level = source.numeric_features.get("z_level", 0.0)
            primary_species = _primary_species(source)
            candidates = by_group.get((z_level, primary_species), [])
            if len(candidates) <= 1:
                candidates = by_z.get(z_level, [])
            source_center = _bounds_center(source)
            nearby = sorted(
                candidates,
                key=lambda item: (
                    _center_distance(source_center, _bounds_center(item)),
                    item.blueprint_id,
                ),
            )[:200]
            all_matches.extend(self._rank_matches(source, nearby, top_k))
        return all_matches

    def _rank_matches(
        self,
        source: SimilarityFeatureVector,
        candidates: list[SimilarityFeatureVector],
        top_k: int,
    ) -> list[SimilarityMatch]:
        scored = []
        for candidate in candidates:
            if candidate.blueprint_id == source.blueprint_id:
                continue
            if candidate.blueprint_type != source.blueprint_type:
                continue
            score = self._score(source, candidate)
            scored.append((candidate.blueprint_id, score))
        scored.sort(key=lambda item: (-item[1].score, item[0]))
        matches = []
        for rank, (candidate_id, score) in enumerate(scored[:top_k], start=1):
            matches.append(
                SimilarityMatch(
                    source_blueprint_id=source.blueprint_id,
                    target_blueprint_id=candidate_id,
                    blueprint_type=source.blueprint_type,
                    score=score.score,
                    rank=rank,
                    explanation=score.explanation,
                    dimensions=score.dimensions,
                    provenance={
                        "source": "BI-4 similarity engine",
                        "generator_version": GENERATOR_VERSION,
                    },
                )
            )
        return matches

    def _candidate_pool(self, source: SimilarityFeatureVector) -> list[SimilarityFeatureVector]:
        same_type = [
            feature
            for feature in self.features.values()
            if feature.blueprint_type == source.blueprint_type
        ]
        if source.blueprint_type == "spawn":
            return self._spawn_candidate_pool(source, same_type)
        if source.blueprint_type == "hunt":
            return self._hunt_candidate_pool(source, same_type)
        return sorted(same_type, key=lambda item: item.blueprint_id)

    def _spawn_candidate_pool(
        self, source: SimilarityFeatureVector, candidates: list[SimilarityFeatureVector]
    ) -> list[SimilarityFeatureVector]:
        monster_name = source.categorical_features.get("monster_name")
        same_species = [
            candidate
            for candidate in candidates
            if candidate.categorical_features.get("monster_name") == monster_name
        ]
        same_species.sort(key=lambda item: (_position_key(item), item.blueprint_id))
        source_key = _position_key(source)
        ranked = sorted(
            same_species,
            key=lambda item: (
                abs(_position_key(item)[0] - source_key[0])
                + abs(_position_key(item)[1] - source_key[1])
                + abs(_position_key(item)[2] - source_key[2]) * 128,
                item.blueprint_id,
            ),
        )
        return ranked[:50]

    def _hunt_candidate_pool(
        self, source: SimilarityFeatureVector, candidates: list[SimilarityFeatureVector]
    ) -> list[SimilarityFeatureVector]:
        source_species = set(source.set_features.get("monster_species", []))
        source_z = source.numeric_features.get("z_level", 0.0)
        ranked = sorted(
            candidates,
            key=lambda item: (
                -len(source_species & set(item.set_features.get("monster_species", []))),
                abs(item.numeric_features.get("z_level", 0.0) - source_z),
                item.blueprint_id,
            ),
        )
        return ranked[:200]

    def _features_by_type(self) -> dict[str, list[SimilarityFeatureVector]]:
        by_type: dict[str, list[SimilarityFeatureVector]] = defaultdict(list)
        for feature in self.features.values():
            by_type[feature.blueprint_type].append(feature)
        for feature_type in ("city", "hunt", "spawn", "dungeon"):
            by_type[feature_type].sort(key=lambda item: item.blueprint_id)
        return by_type

    def _get_feature(self, blueprint_id: str) -> SimilarityFeatureVector:
        try:
            return self.features[blueprint_id]
        except KeyError as exc:
            raise KeyError(f"Unknown blueprint id: {blueprint_id}") from exc

    def _calculate_pattern_recommendation_score(self, target: Blueprint, pattern: Pattern) -> float:
        score = 0.0
        if pattern.category in target.patterns:
            score += 0.4
        if pattern.source == target.provenance.source:
            score += 0.3
        if any(tag in target.regions for tag in pattern.tags):
            score += 0.2
        if pattern.category == target.blueprint_type:
            score += 0.1
        return min(score, 1.0)

    def _get_pattern_recommendation_reasons(self, target: Blueprint, pattern: Pattern) -> list[str]:
        reasons = []
        if pattern.category in target.patterns:
            reasons.append("pattern category in blueprint patterns")
        if pattern.source == target.provenance.source:
            reasons.append("matching source")
        if any(tag in target.regions for tag in pattern.tags):
            reasons.append("tag overlap with regions")
        if pattern.category == target.blueprint_type:
            reasons.append("category matches blueprint type")
        return reasons


def generate_similarity_index(
    dataset_path: str | Path = DEFAULT_DATASET_PATH,
    pattern_catalog_path: str | Path = DEFAULT_PATTERN_CATALOG_PATH,
    output_path: str | Path = DEFAULT_INDEX_PATH,
    stable_output_path: str | Path | None = DEFAULT_STABLE_INDEX_PATH,
) -> SimilarityIndex:
    """Generate and write the BI-4 similarity index."""
    dataset = _read_json(Path(dataset_path))
    pattern_catalog = (
        _read_json(Path(pattern_catalog_path)) if Path(pattern_catalog_path).exists() else {}
    )
    engine = SimilarityEngine()
    index = engine.build_index(
        dataset,
        pattern_catalog,
        source_dataset=Path(dataset_path).name,
        source_pattern_catalog=Path(pattern_catalog_path).name,
    )
    payload = index.to_dict()
    _write_json(Path(output_path), payload)
    if stable_output_path is not None:
        _write_json(Path(stable_output_path), payload)
    return index


def _position_key(feature: SimilarityFeatureVector) -> tuple[float, float, float]:
    return (
        feature.position.get("z") or 0.0,
        feature.position.get("x") or 0.0,
        feature.position.get("y") or 0.0,
    )


def _primary_species(feature: SimilarityFeatureVector) -> str:
    species = sorted(feature.set_features.get("monster_species", []))
    return species[0] if species else ""


def _bounds_center(feature: SimilarityFeatureVector) -> tuple[float, float, float]:
    bounds = feature.bounds
    min_x = bounds.get("min_x") or 0.0
    max_x = bounds.get("max_x") or min_x
    min_y = bounds.get("min_y") or 0.0
    max_y = bounds.get("max_y") or min_y
    min_z = bounds.get("min_z") or 0.0
    max_z = bounds.get("max_z") or min_z
    return ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0, (min_z + max_z) / 2.0)


def _center_distance(
    source: tuple[float, float, float], target: tuple[float, float, float]
) -> float:
    return (
        abs(source[0] - target[0]) + abs(source[1] - target[1]) + abs(source[2] - target[2]) * 128.0
    )


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    generate_similarity_index()


__all__ = ["SimilarityEngine", "generate_similarity_index"]
