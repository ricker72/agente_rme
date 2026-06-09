"""Tests for the Autonomous Visualizer (with mocked matplotlib)."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

from core.autonomous.autonomous_visualizer import AutonomousVisualizer
from core.autonomous.models.design_result import DesignResult
from core.autonomous.models.design_iteration import DesignIteration
from core.autonomous.models.design_plan import DesignPlan
from core.autonomous.models.region_plan import RegionPlan


def _build_result(iteration_scores):
    region = RegionPlan(region_id="r1", region_name="r", region_type="hunt")
    plan = DesignPlan(plan_id="p1", goal_id="g", regions=[region])
    res = DesignResult(result_id="r1", goal_id="g", plan=plan)
    for i, scores in enumerate(iteration_scores):
        res.add_iteration(DesignIteration(
            iteration_id=i, plan_snapshot=plan,
            critic_score=scores[0], playtest_score=scores[1],
            navigation_score=scores[2], density_score=scores[3],
            reuse_score=scores[4],
        ))
    return res


class TestAutonomousVisualizer:
    """Test cases for AutonomousVisualizer."""

    def test_init_creates_directory(self, tmp_path):
        out = str(tmp_path / "viz")
        AutonomousVisualizer(out)
        assert os.path.isdir(out)

    def test_plot_iteration_scores_no_iterations(self, tmp_path):
        out = str(tmp_path / "viz")
        v = AutonomousVisualizer(out)
        result = _build_result([])
        # With no iterations, should return "" (skip plot)
        assert v.plot_iteration_scores(result) == ""

    def test_plot_critic_progress_no_iterations(self, tmp_path):
        out = str(tmp_path / "viz")
        v = AutonomousVisualizer(out)
        result = _build_result([])
        assert v.plot_critic_progress(result) == ""

    def test_plot_optimization_curve_no_iterations(self, tmp_path):
        out = str(tmp_path / "viz")
        v = AutonomousVisualizer(out)
        result = _build_result([])
        assert v.plot_optimization_curve(result) == ""

    def test_plot_iteration_scores_with_mocked_matplotlib(self, tmp_path):
        """When matplotlib is mocked, plot_iteration_scores should return a path."""
        out = str(tmp_path / "viz")
        # Create a fake matplotlib stack
        fake_plt = MagicMock()
        fake_fig = MagicMock()
        fake_plt.subplots.return_value = (fake_fig, MagicMock())
        # Patch _try_matplotlib to return our fake
        with patch("core.autonomous.autonomous_visualizer._try_matplotlib", return_value=fake_plt):
            v = AutonomousVisualizer(out)
            result = _build_result([
                (0.5, 0.6, 0.4, 0.5, 0.5),
                (0.6, 0.7, 0.5, 0.6, 0.6),
                (0.7, 0.8, 0.6, 0.7, 0.7),
            ])
            path = v.plot_iteration_scores(result)
            assert path.endswith("iteration_scores.png")
            fake_plt.subplots.assert_called()
            fake_fig.savefig.assert_called()
            fake_plt.close.assert_called()

    def test_plot_critic_progress_with_mocked_matplotlib(self, tmp_path):
        out = str(tmp_path / "viz")
        fake_plt = MagicMock()
        fake_fig = MagicMock()
        fake_plt.subplots.return_value = (fake_fig, MagicMock())
        with patch("core.autonomous.autonomous_visualizer._try_matplotlib", return_value=fake_plt):
            v = AutonomousVisualizer(out)
            result = _build_result([
                (0.5, 0.6, 0.4, 0.5, 0.5),
                (0.7, 0.8, 0.6, 0.7, 0.7),
            ])
            path = v.plot_critic_progress(result)
            assert path.endswith("critic_progress.png")
            fake_fig.savefig.assert_called()

    def test_plot_optimization_curve_with_mocked_matplotlib(self, tmp_path):
        out = str(tmp_path / "viz")
        fake_plt = MagicMock()
        fake_fig = MagicMock()
        fake_plt.subplots.return_value = (fake_fig, MagicMock())
        with patch("core.autonomous.autonomous_visualizer._try_matplotlib", return_value=fake_plt):
            v = AutonomousVisualizer(out)
            result = _build_result([
                (0.5, 0.6, 0.4, 0.5, 0.5),
                (0.7, 0.8, 0.6, 0.7, 0.7),
            ])
            path = v.plot_optimization_curve(result)
            assert path.endswith("optimization_curve.png")
            fake_fig.savefig.assert_called()
