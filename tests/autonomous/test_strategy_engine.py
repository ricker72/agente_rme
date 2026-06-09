"""Tests for the World Strategy."""

import pytest

from core.autonomous.world_strategy import WorldStrategy, StrategyType


class TestWorldStrategy:
    """Test cases for WorldStrategy."""

    def test_default_weights_balanced(self):
        s = WorldStrategy(strategy_type=StrategyType.BALANCED)
        assert "size" in s.weights
        assert "density" in s.weights
        assert "difficulty" in s.weights

    def test_default_weights_hunt_focused(self):
        s = WorldStrategy(strategy_type=StrategyType.HUNT_FOCUSED)
        assert s.weights.get("hunt_quality", 0) > 0

    def test_default_weights_boss_focused(self):
        s = WorldStrategy(strategy_type=StrategyType.BOSS_FOCUSED)
        assert s.weights.get("boss_quality", 0) > 0

    def test_default_weights_city_focused(self):
        s = WorldStrategy(strategy_type=StrategyType.CITY_FOCUSED)
        assert s.weights.get("city_quality", 0) > 0

    def test_default_weights_campaign_focused(self):
        s = WorldStrategy(strategy_type=StrategyType.CAMPAIGN_FOCUSED)
        assert s.weights.get("storyline", 0) > 0

    def test_default_weights_aggressive_expansion(self):
        s = WorldStrategy(strategy_type=StrategyType.AGGRESSIVE_EXPANSION)
        assert s.weights.get("size", 0) > 0

    def test_apply_strategy_empty(self):
        s = WorldStrategy(strategy_type=StrategyType.BALANCED)
        assert s.apply_strategy({}) == 0.0

    def test_apply_strategy_with_metrics(self):
        s = WorldStrategy(strategy_type=StrategyType.BALANCED)
        metrics = {"size": 0.8, "density": 0.6, "difficulty": 0.5, "navigation": 0.7, "reuse": 0.4}
        score = s.apply_strategy(metrics)
        assert 0.0 < score <= 1.0

    def test_apply_strategy_with_unknown_metrics(self):
        s = WorldStrategy(strategy_type=StrategyType.BALANCED)
        # Unknown metrics still get scored with default 0.1 weight
        score = s.apply_strategy({"unknown_metric": 0.9})
        assert 0.0 < score <= 1.0

    def test_get_set_parameter(self):
        s = WorldStrategy(strategy_type=StrategyType.BALANCED)
        s.set_parameter("key1", "value1")
        assert s.get_parameter("key1") == "value1"
        assert s.get_parameter("missing", "default") == "default"

    def test_to_dict_from_dict(self):
        s = WorldStrategy(strategy_type=StrategyType.BALANCED)
        data = s.to_dict()
        assert data["strategy_type"] == "balanced"
        restored = WorldStrategy.from_dict(data)
        assert restored.strategy_type == StrategyType.BALANCED

    def test_all_strategy_types_initialise(self):
        for st in StrategyType:
            s = WorldStrategy(strategy_type=st)
            assert s.weights
