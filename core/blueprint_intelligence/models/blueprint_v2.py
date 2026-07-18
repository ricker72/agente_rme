# mypy: ignore-errors
"""
Blueprint Intelligence 2.0 — Blueprint model (v2).

A reusable structural blueprint extracted from real Tibia/OpenTibia maps.
Tracks provenance, structural metrics, and semantic metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Provenance:
    """
    Rule 4 compliance: every blueprint must know its origin.
    """

    source: str = ""                          # e.g. "Issavi", "Roshamuul"
    dataset: str = ""                         # e.g. "knowledge_dataset_v3"
    generator_version: str = "2.0"            # Blueprint Intelligence version
    seed: int = 0                             # Random seed used for generation
    extraction_timestamp: str = ""            # ISO-8601 timestamp
    author: str = "blueprint_intelligence"     # Extractor signature

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "dataset": self.dataset,
            "generator_version": self.generator_version,
            "seed": self.seed,
            "extraction_timestamp": self.extraction_timestamp,
            "author": self.author,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Provenance:
        return cls(
            source=data.get("source", ""),
            dataset=data.get("dataset", ""),
            generator_version=data.get("generator_version", "2.0"),
            seed=data.get("seed", 0),
            extraction_timestamp=data.get("extraction_timestamp", ""),
            author=data.get("author", "blueprint_intelligence"),
        )


@dataclass
class BlueprintMetrics:
    """
    Canonical BI-1 structural metrics for a blueprint.

    These values describe what exists in the map. Quality scores live in
    BlueprintScore.
    """

    regions: int = 0
    roads: int = 0
    landmarks: int = 0
    districts: int = 0
    spawn_clusters: int = 0
    waypoints: int = 0
    connectivity_score: float = 0.0
    density_score: float = 0.0
    navigation_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "regions": self.regions,
            "roads": self.roads,
            "landmarks": self.landmarks,
            "districts": self.districts,
            "spawn_clusters": self.spawn_clusters,
            "waypoints": self.waypoints,
            "connectivity_score": self.connectivity_score,
            "density_score": self.density_score,
            "navigation_score": self.navigation_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BlueprintMetrics:
        return cls(
            regions=data.get("regions", 0),
            roads=data.get("roads", 0),
            landmarks=data.get("landmarks", 0),
            districts=data.get("districts", 0),
            spawn_clusters=data.get("spawn_clusters", 0),
            waypoints=data.get("waypoints", 0),
            connectivity_score=data.get("connectivity_score", 0.0),
            density_score=data.get("density_score", 0.0),
            navigation_score=data.get("navigation_score", 0.0),
        )


@dataclass
class BlueprintScore:
    """Canonical BI-1 quality score bundle."""

    pathing_score: float = 0.0
    density_score: float = 0.0
    readability_score: float = 0.0
    progression_score: float = 0.0
    landmark_score: float = 0.0
    exploration_score: float = 0.0
    blueprint_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pathing_score": self.pathing_score,
            "density_score": self.density_score,
            "readability_score": self.readability_score,
            "progression_score": self.progression_score,
            "landmark_score": self.landmark_score,
            "exploration_score": self.exploration_score,
            "blueprint_score": self.blueprint_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BlueprintScore:
        return cls(
            pathing_score=data.get("pathing_score", data.get("navigation_score", 0.0)),
            density_score=data.get("density_score", 0.0),
            readability_score=data.get("readability_score", 0.0),
            progression_score=data.get("progression_score", 0.0),
            landmark_score=data.get("landmark_score", data.get("landmarks_score", 0.0)),
            exploration_score=data.get("exploration_score", 0.0),
            blueprint_score=data.get("blueprint_score", 0.0),
        )


@dataclass
class BlueprintV2:
    """
    Blueprint Intelligence 2.0 — enriched blueprint model.

    Extends the original Blueprint with explicit structural metadata:
      - Regions, roads, landmarks, districts
      - Connectivity / density / navigation scores
      - Provenance (Rule 4)
    """

    # Identity
    blueprint_id: str = ""
    name: str = ""
    type: str = "unknown"          # city, hunt, boss_room, quest_area, dungeon, wilderness
    version: str = "2.0.0"

    # Dimensions
    width: int = 0
    height: int = 0

    # Structural counts
    regions: int = 0
    roads: int = 0
    landmarks: int = 0            # POIs / notable structures
    districts: int = 0
    spawn_clusters: int = 0
    waypoints: int = 0

    # Scoring (Blueprint Scoring Engine)
    connectivity_score: float = 0.0
    density_score: float = 0.0
    navigation_score: float = 0.0
    readability_score: float = 0.0
    progression_score: float = 0.0
    exploration_score: float = 0.0
    blueprint_score: float = 0.0   # Aggregate score

    # Patterns (references into Pattern Library)
    patterns: List[str] = field(default_factory=list)  # pattern names

    # Provenance
    provenance: Provenance = field(default_factory=Provenance)

    # Raw source data (read-only reference)
    _raw: Dict[str, Any] = field(default_factory=dict)

    # Tags
    tags: List[str] = field(default_factory=list)
    description: str = ""

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def metrics(self) -> BlueprintMetrics:
        """Return the canonical structural metrics view."""
        return BlueprintMetrics(
            regions=self.regions,
            roads=self.roads,
            landmarks=self.landmarks,
            districts=self.districts,
            spawn_clusters=self.spawn_clusters,
            waypoints=self.waypoints,
            connectivity_score=self.connectivity_score,
            density_score=self.density_score,
            navigation_score=self.navigation_score,
        )

    @property
    def score(self) -> BlueprintScore:
        """Return the canonical quality score view."""
        return BlueprintScore(
            pathing_score=self.navigation_score,
            density_score=self.density_score,
            readability_score=self.readability_score,
            progression_score=self.progression_score,
            landmark_score=0.0,
            exploration_score=self.exploration_score,
            blueprint_score=self.blueprint_score,
        )

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "blueprint_id": self.blueprint_id,
            "name": self.name,
            "type": self.type,
            "version": self.version,
            "width": self.width,
            "height": self.height,
            "regions": self.regions,
            "roads": self.roads,
            "landmarks": self.landmarks,
            "districts": self.districts,
            "spawn_clusters": self.spawn_clusters,
            "waypoints": self.waypoints,
            "connectivity_score": self.connectivity_score,
            "density_score": self.density_score,
            "navigation_score": self.navigation_score,
            "readability_score": self.readability_score,
            "progression_score": self.progression_score,
            "exploration_score": self.exploration_score,
            "blueprint_score": self.blueprint_score,
            "patterns": self.patterns,
            "provenance": self.provenance.to_dict(),
            "tags": self.tags,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BlueprintV2:
        provenance_raw = data.get("provenance", {})
        provenance = Provenance.from_dict(provenance_raw) if provenance_raw else Provenance()

        return cls(
            blueprint_id=data.get("blueprint_id", ""),
            name=data.get("name", ""),
            type=data.get("type", "unknown"),
            version=data.get("version", "2.0.0"),
            width=data.get("width", 0),
            height=data.get("height", 0),
            regions=data.get("regions", 0),
            roads=data.get("roads", 0),
            landmarks=data.get("landmarks", 0),
            districts=data.get("districts", 0),
            spawn_clusters=data.get("spawn_clusters", 0),
            waypoints=data.get("waypoints", 0),
            connectivity_score=data.get("connectivity_score", 0.0),
            density_score=data.get("density_score", 0.0),
            navigation_score=data.get("navigation_score", 0.0),
            readability_score=data.get("readability_score", 0.0),
            progression_score=data.get("progression_score", 0.0),
            exploration_score=data.get("exploration_score", 0.0),
            blueprint_score=data.get("blueprint_score", 0.0),
            patterns=data.get("patterns", []),
            provenance=provenance,
            tags=data.get("tags", []),
            description=data.get("description", ""),
            _raw=data,
        )
