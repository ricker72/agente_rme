"""
HITO 17 — Blueprint Learner: Automatic blueprint learning from real OTBM maps.

Pipeline:
    OTBM → WorldModel → MapAnalyzer → BlueprintExtractor → PatternMiner → SimilarityEngine → BlueprintCatalog

Capabilities:
    - Detect Temples, Depots, Markets, Boss Rooms, Houses, Bridges, Camps
    - Learn patterns from real maps
    - Find similar blueprints
    - Rank blueprints by quality
    - Save to data/blueprints/
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.analyzer.map_analyzer import MapAnalyzer, MapAnalysis
from core.blueprints.blueprint_extractor import BlueprintExtractor
from core.blueprints.blueprint import Blueprint
from .pattern_miner import PatternMiner, MinedPattern
from .similarity_engine import SimilarityEngine, SimilarityResult
from .blueprint_ranker import BlueprintRanker, RankedBlueprint
from .blueprint_catalog import BlueprintCatalog


@dataclass
class LearningResult:
    """Result of learning blueprints from a map."""

    source_path: str
    success: bool = False
    blueprints: List[Blueprint] = field(default_factory=list)
    mined_patterns: List[MinedPattern] = field(default_factory=list)
    similar_blueprints: List[SimilarityResult] = field(default_factory=list)
    ranked_blueprints: List[RankedBlueprint] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_path": self.source_path,
            "success": self.success,
            "blueprint_count": len(self.blueprints),
            "blueprints": [bp.to_dict() for bp in self.blueprints],
            "mined_patterns": [p.to_dict() for p in self.mined_patterns],
            "similar_blueprints": [s.to_dict() for s in self.similar_blueprints],
            "ranked_blueprints": [r.to_dict() for r in self.ranked_blueprints],
            "stats": self.stats,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class BlueprintLearner:
    """
    Main entry point for automatic blueprint learning from real maps.

    Integrates:
        - OTBMImporter: Load .otbm files
        - MapAnalyzer: Analyze map structure
        - BlueprintExtractor: Extract blueprints
        - PatternMiner: Mine recurring patterns
        - SimilarityEngine: Find similar blueprints
        - BlueprintRanker: Rank by quality/relevance
        - BlueprintCatalog: Store and retrieve blueprints
    """

    # Structure types we can detect
    STRUCTURE_TYPES = [
        "temple",
        "depot",
        "market",
        "boss_room",
        "house",
        "bridge",
        "camp",
        "dungeon_entrance",
        "arena",
        "library",
        "prison",
        "throne_room",
        "crypt",
        "altar",
        "shrine",
        "guildhall",
        "tavern",
        "shop",
        "workshop",
        "farm",
        "mine",
        "cave",
        "ruins",
        "tower",
        "wall_section",
        "gate",
    ]

    def __init__(
        self,
        catalog_dir: str = "data/blueprints/",
        similarity_index_path: str = "data/similarity_index.json",
        pattern_index_path: str = "data/pattern_index.json",
        ranker_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the BlueprintLearner.

        Args:
            catalog_dir: Directory to save/load blueprints
            similarity_index_path: Path to similarity index
            pattern_index_path: Path to pattern index
            ranker_config: Optional configuration for ranking
        """
        self.catalog_dir = Path(catalog_dir)
        self.similarity_index_path = similarity_index_path
        self.pattern_index_path = pattern_index_path

        # Initialize components
        self.extractor = BlueprintExtractor(output_dir=str(catalog_dir))
        self.map_analyzer = MapAnalyzer()
        self.pattern_miner = PatternMiner()
        self.similarity_engine = SimilarityEngine()
        self.ranker = BlueprintRanker(config=ranker_config)
        self.catalog = BlueprintCatalog(catalog_dir)

        # Load existing indexes if available
        self._load_indexes()

        # Built flag
        self._index_built = False

    def _load_indexes(self):
        """Load existing similarity and pattern indexes."""
        if os.path.exists(self.similarity_index_path):
            self.similarity_engine.load_index(self.similarity_index_path)
            self._index_built = True

        if os.path.exists(self.pattern_index_path):
            self.pattern_miner.load_patterns(self.pattern_index_path)

    def learn_from_otbm(
        self,
        otbm_path: str,
        save_blueprints: bool = True,
        find_similar: bool = True,
        rank_results: bool = True,
        min_similarity: float = 0.5,
        top_k_similar: int = 10,
    ) -> LearningResult:
        """
        Learn blueprints from an OTBM file.

        Complete pipeline:
            OTBM → WorldModel → MapAnalysis → BlueprintExtractor
            → PatternMiner → SimilarityEngine → BlueprintRanker → Catalog

        Args:
            otbm_path: Path to .otbm file
            save_blueprints: Whether to save extracted blueprints
            find_similar: Whether to find similar existing blueprints
            rank_results: Whether to rank by quality
            min_similarity: Minimum similarity threshold
            top_k_similar: Number of similar blueprints to return

        Returns:
            LearningResult with all learning outputs
        """
        result = LearningResult(source_path=otbm_path)

        if not os.path.exists(otbm_path):
            result.errors.append(f"File not found: {otbm_path}")
            return result

        source_name = Path(otbm_path).stem
        result.stats["source"] = source_name
        result.stats["timestamp"] = datetime.now().isoformat()

        try:
            # 1. Analyze map
            analysis = self.map_analyzer.analyze(otbm_path)
            result.stats["map_size"] = analysis.map_size
            result.stats["tile_count"] = analysis.tile_count
            result.stats["spawn_count"] = len(analysis.spawns)
            result.stats["house_count"] = len(analysis.houses)
            result.stats["waypoint_count"] = len(analysis.waypoints)
            result.stats["style"] = analysis.style

            # 2. Extract blueprint
            extraction = self.extractor.extract_from_otbm(
                otbm_path, save=save_blueprints
            )

            if not extraction.success:
                result.errors.extend(extraction.errors)
                return result

            result.blueprints.append(extraction.blueprint)
            result.saved_path = extraction.saved_path

            # 3. Mine patterns from the map
            mined = self.pattern_miner.mine_from_analysis(analysis)
            result.mined_patterns = mined

            # 4. Find similar blueprints in catalog
            if find_similar and self.catalog.count() > 0:
                similar = self._find_similar_blueprints(
                    extraction.blueprint,
                    min_similarity=min_similarity,
                    top_k=top_k_similar,
                )
                result.similar_blueprints = similar

            # 5. Rank the blueprint
            if rank_results:
                ranked = self.ranker.rank_blueprints(
                    result.blueprints,
                    reference_patterns=mined,
                    similar_matches=result.similar_blueprints,
                )
                result.ranked_blueprints = ranked

            # 6. Add to catalog
            self.catalog.add_blueprint(extraction.blueprint)

            # 7. Update similarity index
            self._update_similarity_index()

            result.success = True

        except Exception as e:
            result.errors.append(f"Learning error: {e}")

        return result

    def learn_from_analysis(
        self,
        analysis: MapAnalysis,
        save_blueprint: bool = True,
        find_similar: bool = True,
        rank_results: bool = True,
    ) -> LearningResult:
        """
        Learn from an existing MapAnalysis object.

        Args:
            analysis: MapAnalysis from MapAnalyzer
            save_blueprint: Whether to save the blueprint
            find_similar: Whether to find similar blueprints
            rank_results: Whether to rank by quality

        Returns:
            LearningResult
        """
        result = LearningResult(source_path=analysis.source)
        source_name = Path(analysis.source).stem
        result.stats["source"] = source_name
        result.stats["timestamp"] = datetime.now().isoformat()
        result.stats["map_size"] = analysis.map_size
        result.stats["tile_count"] = analysis.tile_count
        result.stats["spawn_count"] = len(analysis.spawns)
        result.stats["house_count"] = len(analysis.houses)
        result.stats["style"] = analysis.style

        try:
            # Extract blueprint
            extraction = self.extractor.extract_from_analysis(
                analysis, save=save_blueprint
            )

            if not extraction.success:
                result.errors.extend(extraction.errors)
                return result

            result.blueprints.append(extraction.blueprint)
            result.saved_path = extraction.saved_path

            # Mine patterns
            mined = self.pattern_miner.mine_from_analysis(analysis)
            result.mined_patterns = mined

            # Find similar
            if find_similar and self.catalog.count() > 0:
                similar = self._find_similar_blueprints(
                    extraction.blueprint, min_similarity=0.5, top_k=10
                )
                result.similar_blueprints = similar

            # Rank
            if rank_results:
                ranked = self.ranker.rank_blueprints(
                    result.blueprints,
                    reference_patterns=mined,
                    similar_matches=result.similar_blueprints,
                )
                result.ranked_blueprints = ranked

            # Add to catalog
            self.catalog.add_blueprint(extraction.blueprint)

            # Update similarity index
            self._update_similarity_index()

            result.success = True

        except Exception as e:
            result.errors.append(f"Learning error: {e}")

        return result

    def learn_batch(
        self,
        otbm_paths: List[str],
        save_blueprints: bool = True,
        find_similar: bool = True,
        rank_results: bool = True,
    ) -> List[LearningResult]:
        """
        Learn from multiple OTBM files.

        Args:
            otbm_paths: List of .otbm file paths
            save_blueprints: Whether to save blueprints
            find_similar: Whether to find similar
            rank_results: Whether to rank

        Returns:
            List of LearningResult
        """
        results = []
        for path in otbm_paths:
            result = self.learn_from_otbm(
                path,
                save_blueprints=save_blueprints,
                find_similar=find_similar,
                rank_results=rank_results,
            )
            results.append(result)

        # After batch, rebuild indexes for cross-map patterns
        self._rebuild_indexes()

        return results

    def _find_similar_blueprints(
        self,
        blueprint: Blueprint,
        min_similarity: float = 0.5,
        top_k: int = 10,
    ) -> List[SimilarityResult]:
        """Find similar blueprints in the catalog."""
        # Create a query vector from blueprint features
        query_vector = self._blueprint_to_vector(blueprint)

        # Search similarity engine
        similar = self.similarity_engine.find_similar_to_vector(
            query_vector, top_k=top_k, min_similarity=min_similarity
        )

        return similar

    def _blueprint_to_vector(self, blueprint: Blueprint) -> List[float]:
        """Convert blueprint to feature vector for similarity search."""
        # Aggregate tile stats
        grounds = {}
        items = {}
        for tile in blueprint.tiles:
            g = f"ground_{tile.ground}"
            grounds[g] = grounds.get(g, 0) + 1
            if tile.item:
                i = f"item_{tile.item}"
                items[i] = items.get(i, 0) + 1

        # Create feature vector
        vector = []

        # Ground distribution (top 20)
        top_grounds = sorted(grounds.items(), key=lambda x: x[1], reverse=True)[:20]
        ground_names = [g for g, _ in top_grounds]
        for name in ground_names:
            vector.append(grounds.get(name, 0) / max(len(blueprint.tiles), 1))
        # Pad to 20
        vector.extend([0.0] * (20 - len(top_grounds)))

        # Item distribution (top 30)
        top_items = sorted(items.items(), key=lambda x: x[1], reverse=True)[:30]
        item_names = [i for i, _ in top_items]
        for name in item_names:
            vector.append(items.get(name, 0) / max(len(blueprint.tiles), 1))
        vector.extend([0.0] * (30 - len(top_items)))

        # Structure features
        vector.append(len(blueprint.rooms) / 10.0)
        vector.append(len(blueprint.zones) / 5.0)
        vector.append(len(blueprint.features) / 10.0)

        # Theme encoding
        theme_vec = self._encode_theme(blueprint.theme)
        vector.extend(theme_vec)

        # Category encoding
        cat_vec = self._encode_category(blueprint.category)
        vector.extend(cat_vec)

        # Metadata
        vector.append(1.0 if blueprint.metadata.hybrid else 0.0)
        vector.append(self._difficulty_to_float(blueprint.metadata.difficulty))

        return vector

    def _encode_theme(self, theme: str) -> List[float]:
        """Encode theme as one-hot vector."""
        themes = [
            "generic",
            "temple",
            "dungeon",
            "city",
            "hunt",
            "issavi",
            "roshamuul",
            "yalahar",
            "jungle",
            "ice",
            "soulwar",
            "library",
            "falcon",
            "cobra",
            "thais",
        ]
        return [1.0 if theme == t else 0.0 for t in themes]

    def _encode_category(self, category: str) -> List[float]:
        """Encode category as one-hot vector."""
        cats = [
            "unknown",
            "temple",
            "dungeon",
            "city",
            "hunting",
            "wilderness",
            "market",
            "bridge",
            "camp",
            "house",
            "boss_room",
            "depot",
            "arena",
        ]
        return [1.0 if category == c else 0.0 for c in cats]

    def _difficulty_to_float(self, difficulty: str) -> float:
        """Convert difficulty to float."""
        difficulties = {
            "safe": 0.1,
            "easy": 0.2,
            "normal": 0.4,
            "hard": 0.6,
            "dangerous": 0.8,
            "deadly": 1.0,
        }
        return difficulties.get(difficulty, 0.5)

    def _update_similarity_index(self):
        """Update similarity index with catalog blueprints."""
        blueprints = self.catalog.list_all()
        if not blueprints:
            return

        # Build embeddings list
        embeddings = []
        for bp in blueprints:
            vector = self._blueprint_to_vector(bp)
            embeddings.append(
                type(
                    "Embedding",
                    (),
                    {
                        "region_id": bp.name,
                        "vector": vector,
                        "region_type": bp.category,
                        "style": bp.theme,
                        "dimensions": bp.size,
                        "embedding_id": bp.name,
                    },
                )()
            )

        # Build region data
        region_data = {}
        for bp in blueprints:
            region_data[bp.name] = bp.to_dict()

        # Build index
        self.similarity_engine.build_index(embeddings, region_data=region_data)
        self._index_built = True

        # Save index
        self.save_indexes()

    def _rebuild_indexes(self):
        """Rebuild all indexes from catalog."""
        self._update_similarity_index()

        # Rebuild pattern index
        blueprints = self.catalog.list_all()
        if blueprints:
            self.pattern_miner.learn_from_blueprints(blueprints)
            self.pattern_miner.save_patterns(self.pattern_index_path)

    def save_indexes(self):
        """Save similarity and pattern indexes to disk."""
        if self._index_built:
            self.similarity_engine.save_index(self.similarity_index_path)

        self.pattern_miner.save_patterns(self.pattern_index_path)

    def query_similar(self, query: str, top_k: int = 10) -> List[SimilarityResult]:
        """
        Natural language query for similar blueprints.

        Supports:
            - "Find maps similar to Roshamuul"
            - "Find temple blueprints"
            - "Show me boss rooms like Throne Room"
            - "Find dungeons with high difficulty"
        """
        return self.similarity_engine.query(query, top_k=top_k)

    def get_blueprint_recommendations(
        self, blueprint_name: str, count: int = 5
    ) -> List[Dict[str, Any]]:
        """Get recommendations for a blueprint."""
        return self.similarity_engine.get_recommendations(blueprint_name, count)

    def get_catalog_stats(self) -> Dict[str, Any]:
        """Get statistics about the blueprint catalog."""
        return self.catalog.get_statistics()

    def get_pattern_guide(self, pattern_type: str = None) -> Dict[str, Any]:
        """Get pattern guide for generation."""
        return self.pattern_miner.generate_pattern_guide(pattern_type)

    def list_available_structures(self) -> List[str]:
        """List structure types we can detect."""
        return self.STRUCTURE_TYPES
