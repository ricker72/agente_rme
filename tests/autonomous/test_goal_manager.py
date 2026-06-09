"""Tests for the Goal Manager."""

import pytest

from core.autonomous.goal_manager import GoalManager, _normalise_target
from core.autonomous.models.design_goal import DesignGoal
from core.autonomous.models.design_iteration import DesignIteration
from core.autonomous.models.design_plan import DesignPlan
from core.autonomous.models.design_result import DesignResult
from core.autonomous.models.region_plan import RegionPlan


def _make_result(critic_scores):
    region = RegionPlan(
        region_id="r1", region_name="r", region_type="hunt",
    )
    plan = DesignPlan(plan_id="p1", goal_id="g", regions=[region])
    res = DesignResult(result_id="r1", goal_id="g", plan=plan)
    for i, score in enumerate(critic_scores):
        res.add_iteration(DesignIteration(
            iteration_id=i, plan_snapshot=plan,
            critic_score=score, playtest_score=0.7,
        ))
    return res


class TestGoalManager:
    """Test cases for GoalManager."""

    def test_add_goal_activates(self):
        gm = GoalManager()
        goal = DesignGoal(prompt="test")
        gm.add_goal(goal)
        assert gm.active_goal is goal

    def test_set_active_goal(self):
        gm = GoalManager()
        gm.add_goal(DesignGoal(prompt="first"))
        gm.add_goal(DesignGoal(prompt="second"))
        assert gm.set_active_goal("second")
        assert gm.active_goal.prompt == "second"

    def test_set_active_goal_not_found(self):
        gm = GoalManager()
        assert not gm.set_active_goal("missing")

    def test_should_stop_on_max_iterations(self):
        gm = GoalManager()
        gm.add_goal(DesignGoal(prompt="t"))
        gm.update_stop_condition("max_iterations", 2)
        res = _make_result([0.5, 0.6, 0.7, 0.8])
        assert gm.should_stop(res, 2)
        assert not gm.should_stop(res, 1)

    def test_should_stop_on_critic_target(self):
        gm = GoalManager()
        gm.add_goal(DesignGoal(prompt="t"))
        gm.update_stop_condition("critic_score", 0.7)
        res = _make_result([0.5, 0.6, 0.8])
        assert gm.should_stop(res, 1)

    def test_should_stop_on_playtest_target(self):
        gm = GoalManager()
        gm.add_goal(DesignGoal(prompt="t"))
        gm.update_stop_condition("playtest_score", 0.7)
        res = _make_result([0.5, 0.6, 0.7])
        res.final_scores["playtest"] = 0.85
        assert gm.should_stop(res, 1)

    def test_should_not_stop_early(self):
        gm = GoalManager()
        gm.add_goal(DesignGoal(prompt="t"))
        res = _make_result([0.5, 0.6])
        assert not gm.should_stop(res, 0)

    def test_should_stop_on_convergence(self):
        gm = GoalManager()
        gm.add_goal(DesignGoal(prompt="t"))
        gm.update_stop_condition("convergence_threshold", 0.01)
        res = _make_result([0.5, 0.5, 0.5])
        # iteration index passed is the 0-based index of the *next* iteration
        # convergence is checked using convergence_data len >= 3
        assert gm.should_stop(res, 3)

    def test_should_stop_on_min_improvement(self):
        gm = GoalManager()
        gm.add_goal(DesignGoal(prompt="t"))
        gm.update_stop_condition("min_improvement", 0.05)
        res = _make_result([0.5, 0.501, 0.501])
        assert gm.should_stop(res, 3)

    def test_normalise_target_zero_to_hundred(self):
        assert _normalise_target(90.0) == pytest.approx(0.9)
        assert _normalise_target(100.0) == 1.0
        assert _normalise_target(0.5) == 0.5
        assert _normalise_target(0.0) == 0.0

    def test_get_progress(self):
        gm = GoalManager()
        gm.add_goal(DesignGoal(prompt="t", target_critic_score=90.0, target_playtest_score=80.0))
        res = _make_result([0.6, 0.7])
        res.final_scores = {"critic": 0.7, "playtest": 0.8, "navigation": 0.5, "density": 0.5, "reuse": 0.5}
        progress = gm.get_progress(res)
        assert progress["critic_score"]["current"] == 0.7
        assert progress["critic_score"]["target"] == pytest.approx(0.9)
        assert progress["iterations"]["max"] == 20
        assert "overall_progress" in progress

    def test_overall_progress_percent(self):
        gm = GoalManager()
        gm.add_goal(DesignGoal(prompt="t", target_critic_score=90.0, target_playtest_score=80.0))
        res = _make_result([0.9])
        res.final_scores = {"critic": 0.9, "playtest": 0.8}
        progress = gm._calculate_overall_progress(res)
        assert 90 <= progress <= 100

    def test_to_dict_from_dict(self):
        gm = GoalManager()
        gm.add_goal(DesignGoal(prompt="t"))
        data = gm.to_dict()
        restored = GoalManager.from_dict(data)
        assert len(restored.goals) == 1
        assert restored.active_goal.prompt == "t"
