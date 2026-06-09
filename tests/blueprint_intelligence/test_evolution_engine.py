"""Tests for BlueprintEvolutionEngine."""

import pytest
from core.blueprints.blueprint import Blueprint, BlueprintTile, BlueprintMetadata
from core.blueprint_intelligence.blueprint_evolution_engine import (
    BlueprintEvolutionEngine,
)


class TestBlueprintEvolutionEngine:
    """Test blueprint evolution and mutation."""

    def setup_method(self):
        self.engine = BlueprintEvolutionEngine(random_seed=42)

    def _make_bp(self, name="test", category="hunt", tiles=None, zones=None, tags=None, raw=None):
        return Blueprint(
            name=name,
            category=category,
            size=(10, 10),
            tiles=tiles or [BlueprintTile(x=0, y=0, ground=100)],
            zones=zones or [],
            metadata=BlueprintMetadata(tags=tags or []),
            _raw=raw or {},
        )

    def test_evolve_improves_score(self):
        """Test evolution improves critic score."""
        bp = self._make_bp("test_hunt", raw={"critic_score": 30.0})
        result = self.engine.evolve(bp, target_critic_score=50.0, max_generations=10)
        assert result.critic_score >= 30.0
        assert result.generation >= 0
        assert result.is_valid

    def test_evolve_reaches_target(self):
        """Test evolution can evolve."""
        bp = self._make_bp("test_target", raw={"critic_score": 60.0})
        result = self.engine.evolve(bp, target_critic_score=80.0, max_generations=15)
        assert result.is_valid
        assert result.fitness > 0

    def test_mutate_expand_region(self):
        """Test expand_region mutation."""
        bp = self._make_bp("expand_test")
        original_size = bp.size
        mutated = self.engine.mutate(bp, "expand_region")
        new_w, new_h = mutated.size
        assert new_w > original_size[0]
        assert new_h > original_size[1]

    def test_mutate_add_hunt(self):
        """Test add_hunt mutation."""
        bp = self._make_bp("add_hunt_test")
        mutated = self.engine.mutate(bp, "add_hunt")
        assert "hunt" in mutated.metadata.tags

    def test_mutate_add_boss(self):
        """Test add_boss mutation adds a zone."""
        bp = self._make_bp("add_boss_test")
        original_zones = len(bp.zones)
        mutated = self.engine.mutate(bp, "add_boss")
        assert len(mutated.zones) > original_zones
        assert mutated.zones[-1]["type"] == "boss_room"

    def test_mutate_change_topology(self):
        """Test change_topology mutation."""
        bp = self._make_bp("topo_test", zones=[
            {"type": "zone", "connections": ["zone_a"]},
            {"type": "zone", "connections": ["zone_b"]},
        ])
        mutated = self.engine.mutate(bp, "change_topology")
        conns = mutated.zones[0].get("connections", [])
        assert len(conns) > 1

    def test_mutate_add_shortcuts(self):
        """Test add_shortcuts mutation."""
        bp = self._make_bp("shortcuts_test")
        mutated = self.engine.mutate(bp, "add_shortcuts")
        assert len(mutated.features) > 0
        assert mutated.features[-1]["type"] == "shortcut"

    def test_mutate_improve_density(self):
        """Test improve_density mutation."""
        bp = self._make_bp("density_test")
        mutated = self.engine.mutate(bp, "improve_density")
        assert mutated is not None

    def test_mutate_improve_critic(self):
        """Test improve_critic_score mutation."""
        bp = self._make_bp("critic_test", raw={"critic_score": 50.0})
        mutated = self.engine.mutate(bp, "improve_critic_score")
        raw_score = mutated._raw.get("critic_score", 0)
        assert raw_score >= 50.0

    def test_estimate_score_improvement(self):
        """Test score improvement estimation."""
        bp = self._make_bp("score_test", raw={"critic_score": 40.0})
        improvement = self.engine.estimate_score_improvement(bp, "improve_density")
        assert isinstance(improvement, float)

    def test_evolve_tracks_mutations(self):
        """Test evolution tracks applied mutations."""
        bp = self._make_bp("track_muts")
        result = self.engine.evolve(bp, target_critic_score=60.0, max_generations=5)
        if result.generation > 0:
            assert len(result.mutations) > 0

    def test_evolve_default_values(self):
        """Test evolve with default parameters."""
        bp = self._make_bp("default_evolve")
        result = self.engine.evolve(bp)
        assert result.is_valid
        assert result.fitness >= 0.0

    def test_calc_complexity(self):
        """Test complexity calculation."""
        bp = self._make_bp("complexity", tiles=[BlueprintTile(x=i, y=0, ground=100) for i in range(20)])
        complexity = self.engine._calc_complexity(bp)
        assert 0.0 <= complexity <= 100.0

    def test_invalid_mutation_falls_back(self):
        """Test invalid mutation type falls back to random."""
        bp = self._make_bp("invalid_mut")
        mutated = self.engine.mutate(bp, "nonexistent_mutation")
        assert mutated is not None