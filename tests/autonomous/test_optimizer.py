"""Tests for the Autonomous Optimizer (iterative design loop)."""

from core.autonomous.autonomous_optimizer import AutonomousOptimizer
from core.autonomous.models.design_goal import DesignGoal
from core.autonomous.models.design_plan import DesignPlan
from core.autonomous.models.region_plan import RegionPlan
from core.autonomous.models.design_iteration import DesignIteration


def _build_simple_plan(goal: DesignGoal) -> DesignPlan:
    plan_id = "test-plan-1"
    regions = []
    for i in range(goal.num_hunts):
        regions.append(
            RegionPlan(
                region_id=f"hunt_{i + 1}",
                region_name=f"Hunt {i + 1}",
                region_type="hunt",
                level_range=goal.level_range,
                target_size=300,
                target_density=0.5,
                target_difficulty=0.4,
            )
        )
    for i in range(goal.num_bosses):
        regions.append(
            RegionPlan(
                region_id=f"boss_{i + 1}",
                region_name=f"Boss {i + 1}",
                region_type="boss",
                level_range=goal.level_range,
                target_size=200,
                target_density=0.7,
                target_difficulty=0.8,
            )
        )
    if not regions:
        regions.append(
            RegionPlan(
                region_id="city_1",
                region_name="Main City",
                region_type="city",
                level_range=goal.level_range,
                target_size=400,
                target_density=0.5,
                target_difficulty=0.1,
            )
        )
    return DesignPlan(plan_id=plan_id, goal_id=goal.prompt, regions=regions)


class TestAutonomousOptimizer:
    """Test cases for AutonomousOptimizer."""

    def test_run_optimization_basic(self):
        optimizer = AutonomousOptimizer(use_real_engines=False)
        optimizer.max_iterations = 1
        goal = DesignGoal(prompt="test", num_hunts=1, num_bosses=1)
        plan = _build_simple_plan(goal)
        result = optimizer.run_optimization(plan, goal)
        assert len(result.iterations) >= 1
        assert "critic" in result.final_scores
        assert "playtest" in result.final_scores

    def test_run_optimization_respects_max_iterations(self):
        optimizer = AutonomousOptimizer(use_real_engines=False)
        optimizer.max_iterations = 3
        goal = DesignGoal(prompt="test", num_hunts=1)
        plan = _build_simple_plan(goal)
        result = optimizer.run_optimization(plan, goal)
        assert len(result.iterations) <= 3

    def test_score_improves_through_iterations(self):
        optimizer = AutonomousOptimizer(use_real_engines=False)
        optimizer.max_iterations = 4
        goal = DesignGoal(prompt="test", num_hunts=1)
        plan = _build_simple_plan(goal)
        result = optimizer.run_optimization(plan, goal)
        stats = optimizer.get_optimization_stats()
        assert "score_improvement" in stats
        assert "score_history" in stats
        assert len(stats["score_history"]) == len(result.iterations)

    def test_optimization_with_world_factory(self):
        from core.world.world_model import WorldModel

        def factory(plan):
            w = WorldModel()
            return w

        optimizer = AutonomousOptimizer(use_real_engines=False)
        optimizer.max_iterations = 1
        goal = DesignGoal(prompt="test", num_hunts=1)
        plan = _build_simple_plan(goal)
        result = optimizer.run_optimization(plan, goal, world_factory=factory)
        assert len(result.iterations) >= 1

    def test_stop_conditions(self):
        optimizer = AutonomousOptimizer(use_real_engines=False)
        optimizer.max_iterations = 10
        optimizer.goal_manager.update_stop_condition("critic_score", 0.5)
        goal = DesignGoal(prompt="test", num_hunts=1)
        plan = _build_simple_plan(goal)
        result = optimizer.run_optimization(plan, goal)
        assert len(result.iterations) <= 10

    def test_to_dict_from_dict(self):
        optimizer = AutonomousOptimizer(use_real_engines=False)
        optimizer.max_iterations = 1
        goal = DesignGoal(prompt="test", num_hunts=1)
        plan = _build_simple_plan(goal)
        optimizer.run_optimization(plan, goal)
        data = optimizer.to_dict()
        assert "goal_manager" in data
        assert "iteration_history" in data
        restored = AutonomousOptimizer.from_dict(data)
        assert len(restored.iteration_history) == len(optimizer.iteration_history)

    def test_evolve_plan_increases_density(self):
        optimizer = AutonomousOptimizer(use_real_engines=False)
        goal = DesignGoal(prompt="test", num_hunts=1)
        plan = _build_simple_plan(goal)
        original_density = plan.regions[0].target_density
        evolved = optimizer._evolve_plan(
            plan, {"density": 0.5, "navigation": 0.5, "critic": 0.5}, goal, 0
        )
        assert evolved.regions[0].target_density >= original_density

    def test_iteration_records_score(self):
        optimizer = AutonomousOptimizer(use_real_engines=False)
        optimizer.max_iterations = 1
        goal = DesignGoal(prompt="test", num_hunts=1)
        plan = _build_simple_plan(goal)
        result = optimizer.run_optimization(plan, goal)
        first = result.iterations[0]
        assert isinstance(first, DesignIteration)
        assert 0.0 <= first.critic_score <= 1.0
        assert 0.0 <= first.playtest_score <= 1.0
