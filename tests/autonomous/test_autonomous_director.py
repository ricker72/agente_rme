"""Tests for the Autonomous Director."""

import pytest

from core.autonomous.autonomous_director import AutonomousDirector, THEME_HINTS
from core.autonomous.models.design_goal import DesignGoal
from core.autonomous.models.region_plan import RegionPlan


class TestAutonomousDirector:
    """Test cases for AutonomousDirector."""

    def test_parse_prompt_simple(self):
        director = AutonomousDirector()
        goal = director.parse_prompt("Create a hunt area")
        assert goal.prompt == "Create a hunt area"
        assert goal.num_hunts >= 1

    def test_parse_prompt_with_level(self):
        director = AutonomousDirector()
        goal = director.parse_prompt("Create a hunt for level 300")
        assert goal.level_range == (250, 350)

    def test_parse_prompt_with_level_range(self):
        director = AutonomousDirector()
        goal = director.parse_prompt("Boss level 300-500")
        assert goal.level_range == (300, 500)

    def test_parse_prompt_with_counts(self):
        director = AutonomousDirector()
        goal = director.parse_prompt("Create 3 hunts and 2 bosses")
        assert goal.num_hunts == 3
        assert goal.num_bosses == 2

    def test_parse_prompt_with_raid(self):
        director = AutonomousDirector()
        goal = director.parse_prompt("Create 1 raid")
        assert goal.num_raids == 1

    def test_parse_prompt_empty_raises(self):
        director = AutonomousDirector()
        with pytest.raises(ValueError):
            director.parse_prompt("")

    def test_parse_prompt_strategy_aggressive(self):
        director = AutonomousDirector()
        goal = director.parse_prompt("Large endgame continent")
        assert goal.strategy == "aggressive_expansion"

    def test_parse_prompt_strategy_city_focused(self):
        director = AutonomousDirector()
        goal = director.parse_prompt("Compact desert city")
        assert goal.strategy == "city_focused"

    def test_decide_regions(self):
        director = AutonomousDirector()
        goal = DesignGoal(
            prompt="Test", num_hunts=2, num_bosses=1, num_raids=1,
        )
        regions = director.decide_regions(goal)
        # 2 hunts + 1 boss + 1 raid + 1 city
        assert len(regions) == 5

        hunt_regions = [r for r in regions if r.region_type == "hunt"]
        boss_regions = [r for r in regions if r.region_type == "boss"]
        raid_regions = [r for r in regions if r.region_type == "raid"]
        city_regions = [r for r in regions if r.region_type == "city"]

        assert len(hunt_regions) == 2
        assert len(boss_regions) == 1
        assert len(raid_regions) == 1
        assert len(city_regions) == 1

    def test_decide_regions_with_zero_counts(self):
        director = AutonomousDirector()
        goal = DesignGoal(
            prompt="Test", num_hunts=0, num_bosses=0, num_raids=0,
        )
        regions = director.decide_regions(goal)
        assert len(regions) == 1
        assert regions[0].region_type == "city"

    def test_select_blueprints(self):
        director = AutonomousDirector()
        region = RegionPlan(
            region_id="test_1", region_name="Test Region", region_type="hunt",
        )
        blueprints = director.select_blueprints(region)
        assert len(blueprints) >= 1
        assert all(isinstance(bp, str) for bp in blueprints)

    def test_select_patterns(self):
        director = AutonomousDirector()
        region = RegionPlan(
            region_id="test_1", region_name="Test Region", region_type="hunt",
        )
        patterns = director.select_patterns(region)
        assert len(patterns) >= 1
        assert all(isinstance(p, str) for p in patterns)

    def test_record_decision(self):
        director = AutonomousDirector()
        director.record_decision("blueprint", "r1", "bp_1", 0.85)
        assert len(director.decision_memory) == 1
        decision = director.decision_memory[0]
        assert decision["decision_type"] == "blueprint"
        assert decision["region_id"] == "r1"
        assert decision["score"] == 0.85
        assert "decision_id" in decision

    def test_get_memory_stats(self):
        director = AutonomousDirector()
        director.record_decision("bp", "r1", "opt1", 0.8)
        director.record_decision("bp", "r2", "opt2", 0.9)
        director.record_decision("bp", "r3", "opt3", 0.7)
        stats = director.get_memory_stats()
        assert stats["total_decisions"] == 3
        assert stats["average_score"] == pytest.approx(0.8, abs=0.01)
        assert stats["best_score"] == 0.9
        assert stats["worst_score"] == 0.7

    def test_get_memory_stats_empty(self):
        director = AutonomousDirector()
        stats = director.get_memory_stats()
        assert stats["total_decisions"] == 0
        assert stats["average_score"] == 0.0

    def test_theme_detection(self):
        director = AutonomousDirector()
        goal = director.parse_prompt("Issavi Roshamuul expansion")
        regions = director.decide_regions(goal)
        # At least one region name should contain the theme
        assert any("Issavi" in r.region_name or "Roshamuul" in r.region_name for r in regions)

    def test_to_dict_from_dict_roundtrip(self):
        director = AutonomousDirector()
        director.record_decision("bp", "r1", "opt1", 0.8)
        data = director.to_dict()
        restored = AutonomousDirector.from_dict(data)
        assert len(restored.decision_memory) == 1
        assert restored.decision_memory[0]["score"] == 0.8

    def test_uses_blueprint_intelligence_when_available(self):
        # Mock blueprint intelligence that returns names
        class MockBI:
            def recommend(self, region_type, top_k=5):
                return [{"name": f"smart_bp_{region_type}_1"}, {"name": f"smart_bp_{region_type}_2"}]

        director = AutonomousDirector(blueprint_intelligence=MockBI())
        region = RegionPlan(region_id="r1", region_name="r1", region_type="hunt")
        bps = director.select_blueprints(region)
        assert any("smart_bp" in bp for bp in bps)

    def test_uses_knowledge_engine_for_patterns(self):
        class MockKE:
            def find_similar_hunts(self, name, k=5):
                return [{"name": "roshamuul_pattern"}]

            def find_similar_cities(self, name, k=5):
                return []
            def find_similar_boss_rooms(self, name, k=5):
                return []
            def find_similar_raids(self, name, k=5):
                return []
            def find_similar_regions(self, name, k=5):
                return []

        director = AutonomousDirector(knowledge_engine=MockKE())
        region = RegionPlan(region_id="r1", region_name="r1", region_type="hunt")
        patterns = director.select_patterns(region)
        assert "roshamuul_pattern" in patterns
