"""Tests for the Autonomous Planner."""

from core.autonomous.autonomous_planner import AutonomousPlanner
from core.autonomous.autonomous_director import AutonomousDirector
from core.autonomous.models.design_goal import DesignGoal
from core.autonomous.models.design_plan import DesignPlan
from core.autonomous.models.region_plan import RegionPlan


class TestAutonomousPlanner:
    """Test cases for AutonomousPlanner."""

    def test_create_plan(self):
        planner = AutonomousPlanner()
        goal = DesignGoal(prompt="Test plan", num_hunts=2, num_bosses=1)
        plan = planner.create_plan(goal)
        assert isinstance(plan, DesignPlan)
        assert plan.goal_id == "Test plan"
        assert len(plan.regions) == 4  # 2 hunts + 1 boss + 1 city

    def test_create_plan_complexity(self):
        planner = AutonomousPlanner()
        goal = DesignGoal(
            prompt="Complex plan",
            num_hunts=3,
            num_bosses=2,
            num_raids=1,
        )
        plan = planner.create_plan(goal)
        assert plan.estimated_complexity > 0
        assert plan.total_estimated_size > 0

    def test_update_plan_add_region(self):
        planner = AutonomousPlanner()
        goal = DesignGoal(prompt="Test", num_hunts=1)
        plan = planner.create_plan(goal)
        initial_count = len(plan.regions)
        new_region = RegionPlan(
            region_id="new_1",
            region_name="New Region",
            region_type="boss",
        )
        updated_plan = planner.update_plan(plan, {"add_region": new_region})
        assert len(updated_plan.regions) == initial_count + 1

    def test_update_plan_remove_region(self):
        planner = AutonomousPlanner()
        goal = DesignGoal(prompt="Test", num_hunts=2)
        plan = planner.create_plan(goal)
        initial_count = len(plan.regions)
        region_to_remove = plan.regions[0].region_id
        updated_plan = planner.update_plan(plan, {"remove_region": region_to_remove})
        assert len(updated_plan.regions) == initial_count - 1

    def test_update_plan_modify_region(self):
        planner = AutonomousPlanner()
        goal = DesignGoal(prompt="Test", num_hunts=1)
        plan = planner.create_plan(goal)
        region_id = plan.regions[0].region_id
        original_density = plan.regions[0].target_density
        updated_plan = planner.update_plan(
            plan,
            {
                "modify_region": {
                    "region_id": region_id,
                    "modifications": {"target_density": 0.9},
                }
            },
        )
        modified_region = updated_plan.get_region(region_id)
        assert modified_region.target_density == 0.9
        assert modified_region.target_density != original_density

    def test_get_plan_summary(self):
        planner = AutonomousPlanner()
        goal = DesignGoal(prompt="Summary test", num_hunts=2, num_bosses=1)
        plan = planner.create_plan(goal)
        summary = planner.get_plan_summary(plan)
        assert "plan_id" in summary
        assert "total_regions" in summary
        assert "region_counts" in summary
        assert "total_estimated_size" in summary
        assert "estimated_complexity" in summary
        assert summary["total_regions"] == 4

    def test_to_dict_from_dict_roundtrip(self):
        planner = AutonomousPlanner()
        data = planner.to_dict()
        restored = AutonomousPlanner.from_dict(data)
        assert isinstance(restored, AutonomousPlanner)

    def test_plan_inherits_director(self):
        director = AutonomousDirector()
        planner = AutonomousPlanner(director=director)
        assert planner.director is director

    def test_create_plan_populates_blueprints(self):
        planner = AutonomousPlanner()
        goal = DesignGoal(prompt="Test", num_hunts=1)
        plan = planner.create_plan(goal)
        for region in plan.regions:
            assert isinstance(region.blueprint_candidates, list)
            assert isinstance(region.patterns, list)
