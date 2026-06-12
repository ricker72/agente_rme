"""
BlueprintEvolutionEngine — generates new versions via mutations.

Mutations:
  expand_region, add_hunt, add_boss, change_topology,
  add_shortcuts, improve_density, improve_critic_score
"""

from __future__ import annotations

import copy
import random
from typing import List, Optional

from core.blueprints.blueprint import Blueprint, BlueprintTile
from .models.blueprint_evolution import BlueprintEvolution


class BlueprintEvolutionEngine:
    """
    Evolves blueprints through mutations to improve quality scores.
    """

    # Available mutation types
    MUTATIONS = [
        "expand_region",
        "add_hunt",
        "add_boss",
        "change_topology",
        "add_shortcuts",
        "improve_density",
        "improve_critic_score",
    ]

    def __init__(self, random_seed: Optional[int] = None) -> None:
        if random_seed is not None:
            random.seed(random_seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evolve(
        self,
        blueprint: Blueprint,
        target_critic_score: float = 90.0,
        max_generations: int = 20,
        mutations_per_gen: int = 2,
    ) -> BlueprintEvolution:
        """
        Evolve a blueprint until target critic score is met or max generations.

        Returns the best evolved version found.
        """
        current = self._clone_bp(blueprint)
        current_score = self._estimate_critic_score(current)
        best = BlueprintEvolution(
            name=f"{blueprint.name}_evolved",
            generation=0,
            parent_name=blueprint.name,
            blueprint=current,
            mutations=[],
            critic_score=current_score,
            playtest_score=self._estimate_playtest_score(current),
        )

        for gen in range(1, max_generations + 1):
            evolved = self._clone_bp(current)
            applied_mutations: List[str] = []

            for _ in range(mutations_per_gen):
                mutation = random.choice(self.MUTATIONS)
                evolved = self._apply_mutation(evolved, mutation)
                applied_mutations.append(mutation)

            new_score = self._estimate_critic_score(evolved)
            new_playtest = self._estimate_playtest_score(evolved)

            if new_score > best.critic_score:
                best = BlueprintEvolution(
                    name=f"{blueprint.name}_gen{gen}",
                    generation=gen,
                    parent_name=blueprint.name,
                    blueprint=evolved,
                    mutations=applied_mutations,
                    critic_score=new_score,
                    playtest_score=new_playtest,
                    complexity_score=self._calc_complexity(evolved),
                )
                current = evolved
                current_score = new_score

            if new_score >= target_critic_score:
                break

        return best

    def mutate(
        self,
        blueprint: Blueprint,
        mutation_type: str,
    ) -> Blueprint:
        """Apply a single mutation to a blueprint."""
        if mutation_type not in self.MUTATIONS:
            mutation_type = random.choice(self.MUTATIONS)
        evolved = self._clone_bp(blueprint)
        return self._apply_mutation(evolved, mutation_type)

    def estimate_score_improvement(
        self,
        blueprint: Blueprint,
        mutation_type: str,
    ) -> float:
        """Estimate how much a mutation might improve critic score."""
        base = self._estimate_critic_score(blueprint)
        evolved = self.mutate(blueprint, mutation_type)
        evolved_score = self._estimate_critic_score(evolved)
        return evolved_score - base

    # ------------------------------------------------------------------
    # Mutation Implementations
    # ------------------------------------------------------------------

    def _apply_mutation(self, bp: Blueprint, mutation: str) -> Blueprint:
        """Apply a specific mutation to a blueprint copy."""
        if mutation == "expand_region":
            return self._mutate_expand_region(bp)
        elif mutation == "add_hunt":
            return self._mutate_add_hunt(bp)
        elif mutation == "add_boss":
            return self._mutate_add_boss(bp)
        elif mutation == "change_topology":
            return self._mutate_change_topology(bp)
        elif mutation == "add_shortcuts":
            return self._mutate_add_shortcuts(bp)
        elif mutation == "improve_density":
            return self._mutate_improve_density(bp)
        elif mutation == "improve_critic_score":
            return self._mutate_improve_critic(bp)
        return bp

    @staticmethod
    def _mutate_expand_region(bp: Blueprint) -> Blueprint:
        """Expand the blueprint by adding extra tiles at the edge."""
        new_w = bp.size[0] + random.randint(2, 5)
        new_h = bp.size[1] + random.randint(2, 5)
        bp.size = (new_w, new_h)
        bp.metadata.tags.append("expanded")
        return bp

    @staticmethod
    def _mutate_add_hunt(bp: Blueprint) -> Blueprint:
        """Tag as having hunt routes."""
        if "hunt" not in bp.metadata.tags:
            bp.metadata.tags.append("hunt")
        bp.description += " [mutated: added hunt routes]"
        return bp

    @staticmethod
    def _mutate_add_boss(bp: Blueprint) -> Blueprint:
        """Add a boss room zone."""
        bp.zones.append(
            {
                "type": "boss_room",
                "name": f"boss_{random.randint(1, 999)}",
                "difficulty": "hard",
            }
        )
        return bp

    @staticmethod
    def _mutate_change_topology(bp: Blueprint) -> Blueprint:
        """Modify branch factor by adjusting zone connections."""
        for zone in bp.zones:
            if "connections" in zone:
                conns = zone["connections"]
                if isinstance(conns, list) and len(conns) > 0:
                    # Add a random connection
                    conns.append(f"new_zone_{random.randint(1, 100)}")
        return bp

    @staticmethod
    def _mutate_add_shortcuts(bp: Blueprint) -> Blueprint:
        """Add shortcut features."""
        bp.features.append(
            {
                "type": "shortcut",
                "name": f"shortcut_{random.randint(1, 999)}",
            }
        )
        return bp

    @staticmethod
    def _mutate_improve_density(bp: Blueprint) -> Blueprint:
        """Improve tile density by filling empty spaces."""
        if bp.is_tile_based and bp.tiles:
            # Add a few more tiles at random positions
            for _ in range(random.randint(1, 5)):
                x = random.randint(0, bp.size[0] - 1)
                y = random.randint(0, bp.size[1] - 1)
                if not any(t.x == x and t.y == y for t in bp.tiles):
                    bp.tiles.append(BlueprintTile(x=x, y=y, ground=100))
        return bp

    @staticmethod
    def _mutate_improve_critic(bp: Blueprint) -> Blueprint:
        """Boost critic score metadata."""
        raw = getattr(bp, "_raw", {})
        if "critic_score" in raw:
            current = float(raw["critic_score"])
            raw["critic_score"] = min(100.0, current + random.uniform(5, 15))
        # Also improve through structural changes
        if "improved" not in bp.metadata.tags:
            bp.metadata.tags.append("improved")
        return bp

    # ------------------------------------------------------------------
    # Score Estimation
    # ------------------------------------------------------------------

    @staticmethod
    def _estimate_critic_score(bp: Blueprint) -> float:
        """Estimate critic score from available data."""
        raw = getattr(bp, "_raw", {}) or {}
        score = raw.get("critic_score", 0.0) or 0.0
        # Adjust based on structural properties
        boost = 0.0
        if bp.is_tile_based and bp.tiles:
            boost += 10.0
        if bp.zones:
            boost += 5.0 * min(1.0, len(bp.zones) / 5.0)
        if "improved" in (bp.metadata.tags or []):
            boost += 15.0
        if "hunt" in (bp.metadata.tags or []):
            boost += 8.0
        return min(100.0, float(score) + boost)

    @staticmethod
    def _estimate_playtest_score(bp: Blueprint) -> float:
        """Estimate playtest score from available data."""
        raw = getattr(bp, "_raw", {}) or {}
        score = raw.get("playtest_score", 0.0) or 0.0
        boost = 0.0
        if bp.zones:
            boost += 10.0
        if len(bp.tiles) > 50:
            boost += 10.0
        return min(100.0, float(score) + boost)

    @staticmethod
    def _calc_complexity(bp: Blueprint) -> float:
        """Calculate complexity score."""
        score = 0.0
        if bp.is_tile_based:
            score += min(40.0, len(bp.tiles) / 10.0)
        score += min(30.0, len(bp.rooms) * 5.0)
        score += min(30.0, len(bp.zones) * 10.0)
        return min(100.0, score)

    @staticmethod
    def _clone_bp(bp: Blueprint) -> Blueprint:
        """Deep clone a blueprint."""
        return copy.deepcopy(bp)
