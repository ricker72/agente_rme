"""Tests for the Autonomous Decision Engine."""

import pytest

from core.autonomous.autonomous_decision_engine import (
    AutonomousDecisionEngine, SCORE_WEIGHTS,
)
from core.autonomous.models.design_goal import DesignGoal
from core.autonomous.models.region_plan import RegionPlan


class TestAutonomousDecisionEngine:
    """Test cases for AutonomousDecisionEngine."""

    def test_select_blueprint(self):
        engine = AutonomousDecisionEngine()
        region = RegionPlan(
            region_id="r1", region_name="Hunt 1", region_type="hunt",
        )
        decision = engine.select_blueprint(region, candidates=["bp_a", "bp_b", "bp_c"])
        assert decision.region_id == "r1"
        assert decision.decision_type == "blueprint"
        assert decision.selected_option in ["bp_a", "bp_b", "bp_c"]
        assert 0.0 <= decision.total_score <= 1.0
        assert decision.confidence > 0.0

    def test_select_blueprint_uses_engine(self):
        class MockBI:
            def recommend(self, region_type, top_k=5):
                return [{"name": "smart_hunt_bp"}]

        engine = AutonomousDecisionEngine(blueprint_intelligence=MockBI())
        region = RegionPlan(region_id="r1", region_name="Hunt", region_type="hunt")
        decision = engine.select_blueprint(region)
        assert "smart_hunt_bp" in [decision.selected_option] + decision.alternatives

    def test_select_pattern(self):
        engine = AutonomousDecisionEngine()
        region = RegionPlan(
            region_id="r1", region_name="Hunt", region_type="hunt",
        )
        decision = engine.select_pattern(region, candidates=["pat_a", "pat_b"])
        assert decision.decision_type == "pattern"
        assert decision.selected_option in ["pat_a", "pat_b"]

    def test_select_cluster(self):
        engine = AutonomousDecisionEngine()
        region = RegionPlan(
            region_id="r1", region_name="Boss", region_type="boss",
        )
        decision = engine.select_cluster(region)
        assert decision.decision_type == "cluster"
        assert "boss" in decision.selected_option

    def test_select_hybrid(self):
        engine = AutonomousDecisionEngine()
        region = RegionPlan(
            region_id="r1", region_name="Hunt", region_type="hunt",
        )
        decision = engine.select_hybrid(region, "bp_a", "bp_b")
        assert decision.decision_type == "hybrid"
        assert "hybrid_hunt" in decision.selected_option
        assert "bp_a" in decision.alternatives
        assert "bp_b" in decision.alternatives

    def test_select_strategy_hunt_focused(self):
        engine = AutonomousDecisionEngine()
        goal = DesignGoal(prompt="test", num_hunts=4)
        strategy = engine.select_strategy(goal)
        assert strategy.strategy_type.value == "hunt_focused"

    def test_select_strategy_boss_focused(self):
        engine = AutonomousDecisionEngine()
        goal = DesignGoal(prompt="test", num_bosses=3, num_hunts=0)
        strategy = engine.select_strategy(goal)
        assert strategy.strategy_type.value == "boss_focused"

    def test_select_strategy_campaign(self):
        engine = AutonomousDecisionEngine()
        goal = DesignGoal(prompt="test", num_raids=3)
        strategy = engine.select_strategy(goal)
        assert strategy.strategy_type.value == "campaign_focused"

    def test_select_strategy_balanced(self):
        engine = AutonomousDecisionEngine()
        goal = DesignGoal(prompt="test", num_hunts=1)
        strategy = engine.select_strategy(goal)
        assert strategy.strategy_type.value == "balanced"

    def test_decision_history_grows(self):
        engine = AutonomousDecisionEngine()
        region = RegionPlan(region_id="r1", region_name="R", region_type="hunt")
        engine.select_blueprint(region)
        engine.select_pattern(region)
        engine.select_cluster(region)
        assert len(engine.decision_history) == 3

    def test_decision_stats(self):
        engine = AutonomousDecisionEngine()
        region = RegionPlan(region_id="r1", region_name="R", region_type="hunt")
        engine.select_blueprint(region)
        engine.select_pattern(region)
        stats = engine.get_decision_stats()
        assert stats["total_decisions"] == 2
        assert "blueprint" in stats["by_type"]
        assert "pattern" in stats["by_type"]
        assert stats["average_score"] > 0

    def test_decision_stats_empty(self):
        engine = AutonomousDecisionEngine()
        stats = engine.get_decision_stats()
        assert stats["total_decisions"] == 0

    def test_to_dict_from_dict(self):
        engine = AutonomousDecisionEngine()
        region = RegionPlan(region_id="r1", region_name="R", region_type="hunt")
        engine.select_blueprint(region)
        data = engine.to_dict()
        restored = AutonomousDecisionEngine.from_dict(data)
        assert len(restored.decision_history) == 1

    def test_pattern_fit_for_region(self):
        engine = AutonomousDecisionEngine()
        region = RegionPlan(region_id="r1", region_name="R", region_type="boss")
        assert engine._pattern_fit("boss_room_alpha", region) >= 0.8
        assert engine._pattern_fit("hunt_alpha", region) < 0.8

    def test_score_weights_sum_to_one(self):
        assert abs(sum(SCORE_WEIGHTS.values()) - 1.0) < 1e-9
