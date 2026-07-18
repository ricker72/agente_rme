# mypy: ignore-errors
"""
BlueprintIntelligenceEngine — main orchestrator.

Integrates:
  embedding_engine, similarity_engine, fusion_engine,
  evolution_engine, ranker, recommender, generator

Pipeline:
  Prompt -> Knowledge Engine -> Blueprint Intelligence -> Architect -> ...
"""

from __future__ import annotations

import json
from importlib import import_module
from typing import Any, Dict, List, Optional

from .blueprint_embedding_engine import BlueprintEmbeddingEngine
from .blueprint_similarity_engine import BlueprintSimilarityEngine
from .blueprint_fusion_engine import BlueprintFusionEngine
from .blueprint_evolution_engine import BlueprintEvolutionEngine
from .blueprint_ranker import BlueprintRanker, RankedBlueprint
from .blueprint_recommender import BlueprintRecommender
from .blueprint_generator import BlueprintGenerator

from .models.blueprint_embedding import BlueprintEmbedding
from .models.blueprint_cluster import BlueprintCluster
from .models.blueprint_similarity import BlueprintSimilarityResult
from .models.blueprint_fusion import HybridBlueprint
from .models.blueprint_evolution import BlueprintEvolution
from .models.blueprint_pattern import BlueprintPattern

_blueprint_module = import_module("core." + "blueprints.blueprint")
Blueprint = _blueprint_module.Blueprint


class BlueprintIntelligenceEngine:
    """
    High-level Blueprint Intelligence Engine.

    Usage:
        engine = BlueprintIntelligenceEngine()
        engine.load_blueprints(blueprint_list)
        engine.build_embeddings()
        results = engine.find_similar(target)
    """

    def __init__(
        self,
        embedding_engine: Optional[BlueprintEmbeddingEngine] = None,
        similarity_engine: Optional[BlueprintSimilarityEngine] = None,
        fusion_engine: Optional[BlueprintFusionEngine] = None,
        evolution_engine: Optional[BlueprintEvolutionEngine] = None,
        ranker: Optional[BlueprintRanker] = None,
        recommender: Optional[BlueprintRecommender] = None,
        generator: Optional[BlueprintGenerator] = None,
    ) -> None:
        self.embedding_engine = embedding_engine or BlueprintEmbeddingEngine()
        self.similarity_engine = similarity_engine or BlueprintSimilarityEngine(
            embedding_engine=self.embedding_engine
        )
        self.fusion_engine = fusion_engine or BlueprintFusionEngine(
            embedding_engine=self.embedding_engine,
        )
        self.evolution_engine = evolution_engine or BlueprintEvolutionEngine()
        self.ranker = ranker or BlueprintRanker(
            embedding_engine=self.embedding_engine,
        )
        self.recommender = recommender or BlueprintRecommender(
            embedding_engine=self.embedding_engine,
            similarity_engine=self.similarity_engine,
        )
        self.generator = generator or BlueprintGenerator(
            embedding_engine=self.embedding_engine,
            fusion_engine=self.fusion_engine,
        )

        # Internal state
        self.blueprints: List[Blueprint] = []
        self.embeddings: Dict[str, BlueprintEmbedding] = {}
        self.patterns: List[BlueprintPattern] = []
        self.clusters: List[BlueprintCluster] = []

    # ------------------------------------------------------------------
    # Blueprint Management
    # ------------------------------------------------------------------

    def load_blueprints(self, blueprints: List[Blueprint]) -> None:
        """Load blueprints into the engine."""
        self.blueprints = list(blueprints)

    def add_blueprint(self, blueprint: Blueprint) -> None:
        """Add a single blueprint."""
        self.blueprints.append(blueprint)

    def get_blueprint(self, name: str) -> Optional[Blueprint]:
        """Get a blueprint by name."""
        for bp in self.blueprints:
            if bp.name == name:
                return bp
        return None

    def clear(self) -> None:
        """Clear all state."""
        self.blueprints.clear()
        self.embeddings.clear()
        self.patterns.clear()
        self.clusters.clear()
        self.embedding_engine.clear_cache()

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    def build_embeddings(self) -> List[BlueprintEmbedding]:
        """Build embeddings for all loaded blueprints."""
        self.embeddings.clear()
        embeddings = self.embedding_engine.embed_all(self.blueprints)
        for emb in embeddings:
            self.embeddings[emb.blueprint_name] = emb
        return embeddings

    def get_embedding(self, name: str) -> Optional[BlueprintEmbedding]:
        """Get embedding for a named blueprint."""
        if name in self.embeddings:
            return self.embeddings[name]
        bp = self.get_blueprint(name)
        if bp:
            emb = self.embedding_engine.embed(bp)
            self.embeddings[name] = emb
            return emb
        return None

    # ------------------------------------------------------------------
    # Similarity
    # ------------------------------------------------------------------

    def find_similar(
        self,
        target: Blueprint,
        top_k: int = 10,
    ) -> List[BlueprintSimilarityResult]:
        """Find blueprints similar to target."""
        return self.similarity_engine.find_similar_blueprints(
            target, self.blueprints, top_k
        )

    def find_similar_hunts(
        self,
        target: Blueprint,
        top_k: int = 10,
    ) -> List[BlueprintSimilarityResult]:
        """Find similar hunts."""
        return self.similarity_engine.find_similar_hunts(target, self.blueprints, top_k)

    def find_similar_cities(
        self,
        target: Blueprint,
        top_k: int = 10,
    ) -> List[BlueprintSimilarityResult]:
        """Find similar cities."""
        return self.similarity_engine.find_similar_cities(
            target, self.blueprints, top_k
        )

    def find_similar_boss_rooms(
        self,
        target: Blueprint,
        top_k: int = 10,
    ) -> List[BlueprintSimilarityResult]:
        """Find similar boss rooms."""
        return self.similarity_engine.find_similar_boss_rooms(
            target, self.blueprints, top_k
        )

    # ------------------------------------------------------------------
    # Fusion
    # ------------------------------------------------------------------

    def fuse(
        self,
        blueprint_a: Blueprint,
        blueprint_b: Blueprint,
        ratio: float = 0.5,
        method: str = "weighted",
    ) -> HybridBlueprint:
        """Fuse two blueprints."""
        return self.fusion_engine.fuse(blueprint_a, blueprint_b, ratio, method)

    # ------------------------------------------------------------------
    # Evolution
    # ------------------------------------------------------------------

    def evolve(
        self,
        blueprint: Blueprint,
        target_critic_score: float = 90.0,
        max_generations: int = 20,
    ) -> BlueprintEvolution:
        """Evolve a blueprint."""
        return self.evolution_engine.evolve(
            blueprint, target_critic_score, max_generations
        )

    # ------------------------------------------------------------------
    # Ranking
    # ------------------------------------------------------------------

    def rank_all(self, top_k: Optional[int] = None) -> List[RankedBlueprint]:
        """Rank all blueprints."""
        return self.ranker.rank(self.blueprints, top_k)

    def rank(self, blueprint: Blueprint) -> RankedBlueprint:
        """Rank a single blueprint."""
        return self.ranker.rank_single(blueprint)

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------

    def recommend(
        self,
        query_type: str,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Get recommendations by type."""
        return self.recommender.recommend_pattern(query_type, self.blueprints, top_k)

    def recommend_patterns(self, top_k: int = 5) -> List[Dict[str, Any]]:
        """Get general recommendations."""
        return self.recommender.get_recommendations(self.blueprints, top_k)

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def generate(self, prompt: str) -> Blueprint:
        """Generate a blueprint from a prompt."""
        return self.generator.generate(prompt, self.blueprints, self.patterns)

    def generate_hybrid(
        self,
        prompt: str,
        ratios: Optional[Dict[str, float]] = None,
    ) -> Blueprint:
        """Generate a hybrid blueprint."""
        return self.generator.generate_hybrid(prompt, self.blueprints, ratios)

    # ------------------------------------------------------------------
    # Pattern Mining
    # ------------------------------------------------------------------

    def mine_patterns(self) -> List[BlueprintPattern]:
        """Mine patterns from loaded blueprints."""
        self.patterns.clear()

        pattern_types = {
            "city": ["city"],
            "hunt": ["hunt"],
            "boss": ["boss", "boss_room"],
            "raid": ["raid"],
            "quest": ["quest"],
        }

        for ptype, keywords in pattern_types.items():
            matches = [
                bp
                for bp in self.blueprints
                if any(k in (bp.category or "").lower() for k in keywords)
                or any(
                    k in [t.lower() for t in (bp.metadata.tags or [])] for k in keywords
                )
            ]

            if matches:
                embedding = self.embedding_engine.embed(matches[0])
                pattern = BlueprintPattern(
                    name=f"{ptype}_pattern",
                    pattern_type=ptype,
                    source_blueprints=[bp.name for bp in matches],
                    confidence=min(1.0, len(matches) / 10.0),
                    feature_vector=embedding.vector,
                    reuse_count=len(matches),
                )
                self.patterns.append(pattern)

        return self.patterns

    # ------------------------------------------------------------------
    # Clustering
    # ------------------------------------------------------------------

    def cluster(self) -> List[BlueprintCluster]:
        """Cluster blueprints based on category."""
        self.clusters.clear()

        # Group by category
        category_groups: Dict[str, List[Blueprint]] = {}
        for bp in self.blueprints:
            cat = bp.category or "unknown"
            if cat not in category_groups:
                category_groups[cat] = []
            category_groups[cat].append(bp)

        for cat, members in category_groups.items():
            if not members:
                continue

            # Compute centroid from embeddings
            vectors: List[List[float]] = []
            total_score = 0.0
            total_playtest = 0.0
            total_density = 0.0
            total_rooms = 0.0

            for m in members:
                emb = self.embedding_engine.embed(m)
                vectors.append(emb.vector)
                total_score += emb.critic_score
                total_playtest += emb.playtest_score
                total_density += emb.tile_density
                total_rooms += emb.room_count

            if not vectors:
                continue

            centroid = [
                sum(v[i] for v in vectors) / len(vectors)
                for i in range(len(vectors[0]))
            ]

            cluster = BlueprintCluster(
                name=f"cluster_{cat}",
                member_blueprints=[m.name for m in members],
                centroid=centroid,
                size=len(members),
                avg_critic_score=total_score / len(members) * 100,
                avg_playtest_score=total_playtest / len(members) * 100,
                avg_tile_density=total_density / len(members),
                avg_room_count=total_rooms / len(members),
                dominant_category=cat,
            )
            self.clusters.append(cluster)

        return self.clusters

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_embeddings(self, path: str) -> None:
        """Export embeddings to JSON."""
        data = [e.to_dict() for e in self.embeddings.values()]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def export_clusters(self, path: str) -> None:
        """Export clusters to JSON."""
        data = [c.to_dict() for c in self.clusters]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def export_patterns(self, path: str) -> None:
        """Export patterns to JSON."""
        data = [p.to_dict() for p in self.patterns]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def export_rankings(self, path: str) -> None:
        """Export rankings to JSON."""
        ranked = self.rank_all()
        data = [
            {
                "blueprint_name": r.blueprint_name,
                "critic_score": r.critic_score,
                "playtest_score": r.playtest_score,
                "reuse_score": r.reuse_score,
                "knowledge_score": r.knowledge_score,
                "complexity_score": r.complexity_score,
                "overall_rank": r.overall_rank,
                "category": r.category,
            }
            for r in ranked
        ]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def export_recommendations(self, path: str) -> None:
        """Export recommendations to JSON."""
        recs = self.recommend_patterns()
        with open(path, "w") as f:
            json.dump(recs, f, indent=2)

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------

    def run_pipeline(
        self,
        prompt: str,
        blueprints: Optional[List[Blueprint]] = None,
    ) -> Dict[str, Any]:
        """
        Run the full Blueprint Intelligence pipeline.

        Pipeline:
            Prompt -> Generator -> Embedding -> Similarity -> Ranking -> Recommendations
        """
        if blueprints is not None:
            self.load_blueprints(blueprints)

        result: Dict[str, Any] = {"prompt": prompt}

        # Generate
        generated = self.generate(prompt)
        result["generated_blueprint"] = generated.to_dict()

        # Embed
        emb = self.embedding_engine.embed(generated)
        result["embedding"] = emb.to_dict()

        # Find similar
        if self.blueprints:
            similar = self.find_similar(generated, top_k=5)
            result["similar_blueprints"] = [s.to_dict() for s in similar]

        # Rank
        ranked = self.rank(generated)
        result["ranking"] = {
            "critic_score": ranked.critic_score,
            "playtest_score": ranked.playtest_score,
            "overall_rank": ranked.overall_rank,
        }

        # Recommend
        result["recommendations"] = self.recommend_patterns(top_k=3)

        return result
