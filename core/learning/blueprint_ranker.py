"""
HITO 17 — Blueprint Ranker: Ranks blueprints by quality, relevance, and utility.

Ranking criteria:
- Structural completeness (rooms, zones, features present)
- Tile density and coverage
- Pattern consistency with mined patterns
- Similarity to high-quality reference blueprints
- Metadata richness (theme, difficulty, tags)
- Generation suitability
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from core.blueprints.blueprint import Blueprint
from .pattern_miner import PatternMiner, MinedPattern
from .similarity_engine import SimilarityResult


@dataclass
class RankedBlueprint:
    """A blueprint with its ranking score and breakdown."""
    blueprint: Blueprint
    overall_score: float
    score_breakdown: Dict[str, float]
    rank: int
    percentile: float
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "blueprint": self.blueprint.to_dict(),
            "overall_score": self.overall_score,
            "score_breakdown": self.score_breakdown,
            "rank": self.rank,
            "percentile": self.percentile,
            "recommendations": self.recommendations,
        }


class BlueprintRanker:
    """
    Ranks blueprints by multiple quality criteria.
    
    Scoring components:
    1. Structural Completeness (0-1): Has rooms, zones, features, entry point
    2. Tile Quality (0-1): Tile count, density, ground/item variety
    3. Pattern Consistency (0-1): Matches mined patterns
    4. Metadata Richness (0-1): Theme, difficulty, tags, capacity
    5. Similarity Bonus (0-1): Similar to high-quality blueprints
    6. Generation Suitability (0-1): Good for procedural generation
    """
    
    # Weights for each scoring component (must sum to 1.0)
    DEFAULT_WEIGHTS = {
        "structural_completeness": 0.25,
        "tile_quality": 0.20,
        "pattern_consistency": 0.20,
        "metadata_richness": 0.15,
        "similarity_bonus": 0.10,
        "generation_suitability": 0.10,
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the ranker.
        
        Args:
            config: Optional configuration dict with:
                - weights: custom scoring weights
                - min_tile_count: minimum tiles for good score
                - reference_blueprints: list of high-quality blueprint names
        """
        self.config = config or {}
        self.weights = self.config.get("weights", self.DEFAULT_WEIGHTS.copy())
        self.min_tile_count = self.config.get("min_tile_count", 50)
        self.reference_names = self.config.get("reference_blueprints", [])
        self.reference_blueprints: List[Blueprint] = []
        
        # Normalize weights
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}
    
    def set_reference_blueprints(self, blueprints: List[Blueprint]):
        """Set reference blueprints for similarity comparison."""
        self.reference_blueprints = blueprints
    
    def rank_blueprints(
        self,
        blueprints: List[Blueprint],
        reference_patterns: List[MinedPattern] = None,
        similar_matches: List[SimilarityResult] = None,
    ) -> List[RankedBlueprint]:
        """
        Rank a list of blueprints.
        
        Args:
            blueprints: Blueprints to rank
            reference_patterns: Mined patterns to check consistency against
            similar_matches: Similar blueprints found in catalog
            
        Returns:
            List of RankedBlueprint sorted by score (highest first)
        """
        if not blueprints:
            return []
        
        ranked = []
        
        for bp in blueprints:
            # Compute individual scores
            scores = {}
            
            # 1. Structural Completeness
            scores["structural_completeness"] = self._score_structural_completeness(bp)
            
            # 2. Tile Quality
            scores["tile_quality"] = self._score_tile_quality(bp)
            
            # 3. Pattern Consistency
            scores["pattern_consistency"] = self._score_pattern_consistency(bp, reference_patterns)
            
            # 4. Metadata Richness
            scores["metadata_richness"] = self._score_metadata_richness(bp)
            
            # 5. Similarity Bonus
            scores["similarity_bonus"] = self._score_similarity_bonus(
                bp, similar_matches or []
            )
            
            # 6. Generation Suitability
            scores["generation_suitability"] = self._score_generation_suitability(bp)
            
            # Overall weighted score
            overall = sum(scores[k] * self.weights.get(k, 0) for k in scores)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(bp, scores)
            
            ranked.append(RankedBlueprint(
                blueprint=bp,
                overall_score=overall,
                score_breakdown=scores,
                rank=0,  # Will be set after sorting
                percentile=0.0,
                recommendations=recommendations,
            ))
        
        # Sort by overall score descending
        ranked.sort(key=lambda r: r.overall_score, reverse=True)
        
        # Assign ranks and percentiles
        for i, ranked_bp in enumerate(ranked):
            ranked_bp.rank = i + 1
            ranked_bp.percentile = 1.0 - (i / max(len(ranked) - 1, 1))
        
        return ranked
    
    def _score_structural_completeness(self, bp: Blueprint) -> float:
        """Score how complete the blueprint structure is."""
        score = 0.0
        
        # Has tiles
        if bp.tiles:
            score += 0.3
            if len(bp.tiles) >= self.min_tile_count:
                score += 0.2
        
        # Has entry point
        if bp.entry is not None:
            score += 0.15
        
        # Has rooms
        if bp.rooms:
            score += 0.15
            room_coverage = sum(r.get("area", 0) for r in bp.rooms)
            if room_coverage > 0 and bp.area > 0:
                score += min(0.1, room_coverage / bp.area)
        
        # Has zones
        if bp.zones:
            score += 0.1
        
        # Has features
        if bp.features:
            score += 0.1
        
        return min(1.0, score)
    
    def _score_tile_quality(self, bp: Blueprint) -> float:
        """Score tile quality and variety."""
        if not bp.tiles:
            return 0.0
        
        score = 0.0
        tile_count = len(bp.tiles)
        
        # Tile count score
        if tile_count >= 100:
            score += 0.3
        elif tile_count >= 50:
            score += 0.2
        elif tile_count >= 20:
            score += 0.1
        
        # Ground variety
        grounds = set(t.ground for t in bp.tiles if t.ground != 0)
        ground_score = min(1.0, len(grounds) / 10.0) * 0.25
        score += ground_score
        
        # Item variety
        items = set(t.item for t in bp.tiles if t.item is not None)
        item_score = min(1.0, len(items) / 15.0) * 0.25
        score += item_score
        
        # Tile density (tiles per area)
        if bp.area > 0:
            density = tile_count / bp.area
            if 0.3 <= density <= 0.9:
                score += 0.2
            elif density > 0:
                score += 0.1
        
        return min(1.0, score)
    
    def _score_pattern_consistency(
        self, 
        bp: Blueprint, 
        reference_patterns: List[MinedPattern] = None
    ) -> float:
        """Score consistency with mined patterns."""
        if not reference_patterns:
            # Use category/theme to check against expected patterns
            return self._score_pattern_by_type(bp)
        
        max_consistency = 0.0
        
        for pattern in reference_patterns:
            consistency = self._compare_blueprint_to_pattern(bp, pattern)
            max_consistency = max(max_consistency, consistency)
        
        return max_consistency
    
    def _score_pattern_by_type(self, bp: Blueprint) -> float:
        """Score based on expected patterns for blueprint type."""
        # Define expected elements per category
        expected = {
            "temple": {
                "grounds": [415],  # polished_stone
                "items": [101, 102, 108, 109],  # walls, pillars
                "min_rooms": 1,
                "has_entrance": True,
            },
            "depot": {
                "items": [5000, 5001],  # depot lockers
                "open_space": True,
            },
            "market": {
                "items": [1210, 1211],  # stalls, counters
                "npcs": True,
            },
            "boss_room": {
                "items": [101, 102, 108],  # arena walls
                "spawns": True,
                "single_room": True,
            },
            "house": {
                "rooms": True,
                "residential_items": True,
            },
            "bridge": {
                "linear": True,
                "railings": [101, 102],
            },
            "camp": {
                "items": [1000, 1001],  # campfire, tents
                "perimeter": True,
            },
        }
        
        category = bp.category.lower()
        if category not in expected:
            return 0.5  # neutral for unknown types
        
        exp = expected[category]
        score = 0.0
        checks = 0
        
        # Check grounds
        if "grounds" in exp:
            checks += 1
            bp_grounds = set(t.ground for t in bp.tiles)
            if any(g in bp_grounds for g in exp["grounds"]):
                score += 1.0
        
        # Check items
        if "items" in exp:
            checks += 1
            bp_items = set(t.item for t in bp.tiles if t.item is not None)
            if any(i in bp_items for i in exp["items"]):
                score += 1.0
        
        # Check rooms
        if "min_rooms" in exp:
            checks += 1
            if len(bp.rooms) >= exp["min_rooms"]:
                score += 1.0
        
        # Check entrance
        if "has_entrance" in exp:
            checks += 1
            if bp.entry is not None:
                score += 1.0
        
        # Check spawns
        if "spawns" in exp:
            checks += 1
            has_spawn = any(t.spawn for t in bp.tiles)
            if has_spawn:
                score += 1.0
        
        return score / max(checks, 1)
    
    def _compare_blueprint_to_pattern(self, bp: Blueprint, pattern: MinedPattern) -> float:
        """Compare a blueprint to a mined pattern."""
        scores = []
        
        # Required grounds
        if pattern.required_grounds:
            bp_grounds = set(t.ground for t in bp.tiles)
            matches = sum(1 for g in pattern.required_grounds if g in bp_grounds)
            scores.append(matches / len(pattern.required_grounds))
        
        # Required items
        if pattern.required_items:
            bp_items = set(t.item for t in bp.tiles if t.item is not None)
            matches = sum(1 for i in pattern.required_items if i in bp_items)
            scores.append(matches / len(pattern.required_items))
        
        # Layout preference
        # Check if blueprint layout matches pattern preference
        layout_pref = pattern.generation_hints.get("layout_preference", "organic")
        bp_layout = self._infer_layout_from_blueprint(bp)
        if bp_layout == layout_pref:
            scores.append(1.0)
        elif bp_layout in ["grid", "linear", "radial", "organic"]:
            scores.append(0.5)
        else:
            scores.append(0.0)
        
        # Size compatibility
        bp_area = bp.area
        pattern_area = pattern.typical_size[0] * pattern.typical_size[1]
        if pattern_area > 0:
            ratio = min(bp_area, pattern_area) / max(bp_area, pattern_area)
            scores.append(ratio)
        
        return np.mean(scores) if scores else 0.5
    
    def _infer_layout_from_blueprint(self, bp: Blueprint) -> str:
        """Infer layout type from blueprint structure."""
        if not bp.tiles:
            return "unknown"
        
        # Get tile positions
        positions = [(t.x, t.y) for t in bp.tiles]
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        
        x_span = max(xs) - min(xs) if xs else 0
        y_span = max(ys) - min(ys) if ys else 0
        
        if x_span == 0 or y_span == 0:
            return "linear"
        
        # Check grid patterns
        unique_x = len(set(xs))
        unique_y = len(set(ys))
        
        if unique_x > 3 and unique_y > 3:
            var_x = np.var(xs)
            var_y = np.var(ys)
            if var_x < (x_span ** 2) * 0.1 and var_y < (y_span ** 2) * 0.1:
                return "grid"
        
        # Check linear
        if x_span > y_span * 3 or y_span > x_span * 3:
            return "linear"
        
        # Check radial (tiles around center)
        center_x = np.mean(xs)
        center_y = np.mean(ys)
        distances = [np.sqrt((x - center_x)**2 + (y - center_y)**2) for x, y in positions]
        if np.std(distances) < np.mean(distances) * 0.3:
            return "radial"
        
        return "organic"
    
    def _score_metadata_richness(self, bp: Blueprint) -> float:
        """Score metadata completeness."""
        score = 0.0
        
        meta = bp.metadata
        
        # Style
        if meta.style:
            score += 0.2
        
        # Era
        if meta.era:
            score += 0.1
        
        # Difficulty
        if meta.difficulty and meta.difficulty != "safe":
            score += 0.15
        
        # Tags
        if meta.tags:
            score += min(0.25, len(meta.tags) * 0.05)
        
        # Capacity
        if meta.capacity:
            score += 0.1
        
        # Hybrid flag
        if meta.hybrid:
            score += 0.1
        
        # Description
        if bp.description and len(bp.description) > 20:
            score += 0.1
        
        # Version
        if bp.version:
            score += 0.05
        
        return min(1.0, score)
    
    def _score_similarity_bonus(
        self, 
        bp: Blueprint, 
        similar_matches: List[SimilarityResult]
    ) -> float:
        """Score based on similarity to known good blueprints."""
        if not similar_matches:
            return 0.0
        
        # Average similarity of top matches
        top_scores = [m.similarity_score for m in similar_matches[:5]]
        avg_score = np.mean(top_scores) if top_scores else 0.0
        
        # Bonus for high similarity
        return min(1.0, avg_score * 1.2)
    
    def _score_generation_suitability(self, bp: Blueprint) -> float:
        """Score how suitable the blueprint is for procedural generation."""
        score = 0.0
        
        # Tile-based format is better for generation
        if bp.is_tile_based:
            score += 0.3
        
        # Reasonable size
        if 100 <= bp.area <= 5000:
            score += 0.2
        elif bp.area > 0:
            score += 0.1
        
        # Has clear structure (rooms + features)
        if bp.rooms and bp.features:
            score += 0.2
        
        # Distinct theme
        if bp.theme not in ["generic", "unknown"]:
            score += 0.15
        
        # Balanced difficulty
        diff_weights = {"safe": 0.05, "easy": 0.1, "normal": 0.15, "hard": 0.1, "dangerous": 0.05}
        score += diff_weights.get(bp.metadata.difficulty, 0.05)
        
        # Has entry point for placement
        if bp.entry:
            score += 0.15
        
        return min(1.0, score)
    
    def _generate_recommendations(self, bp: Blueprint, scores: Dict[str, float]) -> List[str]:
        """Generate improvement recommendations."""
        recs = []
        
        if scores.get("structural_completeness", 0) < 0.6:
            recs.append("Add more structures: rooms, zones, features")
        
        if scores.get("tile_quality", 0) < 0.5:
            if len(bp.tiles) < self.min_tile_count:
                recs.append(f"Increase tile count (current: {len(bp.tiles)}, target: {self.min_tile_count}+)")
            grounds = set(t.ground for t in bp.tiles)
            if len(grounds) < 3:
                recs.append("Add more ground variety")
            items = set(t.item for t in bp.tiles if t.item)
            if len(items) < 5:
                recs.append("Add more item variety")
        
        if scores.get("pattern_consistency", 0) < 0.5:
            recs.append(f"Improve consistency with {bp.category} patterns")
        
        if scores.get("metadata_richness", 0) < 0.5:
            if not bp.metadata.tags:
                recs.append("Add descriptive tags")
            if bp.metadata.difficulty == "safe":
                recs.append("Set appropriate difficulty level")
        
        if scores.get("generation_suitability", 0) < 0.5:
            if not bp.is_tile_based:
                recs.append("Convert to tile-based format for better generation")
            if not bp.entry:
                recs.append("Define entry point for placement")
        
        return recs
    
    def get_ranking_summary(self, ranked: List[RankedBlueprint]) -> Dict[str, Any]:
        """Get summary statistics of ranked blueprints."""
        if not ranked:
            return {}
        
        scores = [r.overall_score for r in ranked]
        
        return {
            "total_ranked": len(ranked),
            "avg_score": np.mean(scores),
            "median_score": np.median(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "std_dev": np.std(scores),
            "top_blueprint": ranked[0].blueprint.name if ranked else None,
            "score_distribution": {
                "excellent": sum(1 for s in scores if s >= 0.8),
                "good": sum(1 for s in scores if 0.6 <= s < 0.8),
                "fair": sum(1 for s in scores if 0.4 <= s < 0.6),
                "poor": sum(1 for s in scores if s < 0.4),
            },
        }
    
    def save_rankings(self, ranked: List[RankedBlueprint], output_path: str):
        """Save rankings to JSON file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        data = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "weights": self.weights,
            "rankings": [r.to_dict() for r in ranked],
            "summary": self.get_ranking_summary(ranked),
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)