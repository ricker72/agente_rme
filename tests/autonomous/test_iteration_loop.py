"""Tests for the iterative design loop end-to-end."""

import json

from core.autonomous import AutonomousWorldDesigner
from core.autonomous.models.design_iteration import DesignIteration


class TestIterationLoop:
    """Tests for the iterative design loop."""

    def test_generate_runs_at_least_one_iteration(self, tmp_path):
        designer = AutonomousWorldDesigner(output_dir=str(tmp_path / "autonomous"))
        designer.optimizer.use_real_engines = False
        result = designer.generate("Simple hunt level 200", max_iterations=2)
        assert len(result.iterations) >= 1
        for it in result.iterations:
            assert isinstance(it, DesignIteration)

    def test_convergence_data_is_recorded(self, tmp_path):
        designer = AutonomousWorldDesigner(output_dir=str(tmp_path / "autonomous"))
        designer.optimizer.use_real_engines = False
        result = designer.generate("Hunt 200", max_iterations=3)
        assert len(result.convergence_data) == len(result.iterations)
        assert all(0.0 <= s <= 1.0 for s in result.convergence_data)

    def test_iteration_scores_are_normalised(self, tmp_path):
        designer = AutonomousWorldDesigner(output_dir=str(tmp_path / "autonomous"))
        designer.optimizer.use_real_engines = False
        result = designer.generate("Boss 200", max_iterations=2)
        for it in result.iterations:
            assert 0.0 <= it.critic_score <= 1.0
            assert 0.0 <= it.playtest_score <= 1.0
            assert 0.0 <= it.navigation_score <= 1.0
            assert 0.0 <= it.density_score <= 1.0
            assert 0.0 <= it.reuse_score <= 1.0

    def test_exports_history_json(self, tmp_path):
        designer = AutonomousWorldDesigner(output_dir=str(tmp_path / "autonomous"))
        designer.optimizer.use_real_engines = False
        designer.generate("Hunt 200", max_iterations=1)
        history = tmp_path / "autonomous" / "autonomous_history.json"
        assert history.exists()
        with open(history, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_exports_decisions_json(self, tmp_path):
        designer = AutonomousWorldDesigner(output_dir=str(tmp_path / "autonomous"))
        designer.optimizer.use_real_engines = False
        designer.generate("Hunt 200", max_iterations=1)
        decisions = tmp_path / "autonomous" / "autonomous_decisions.json"
        assert decisions.exists()

    def test_exports_iterations_json(self, tmp_path):
        designer = AutonomousWorldDesigner(output_dir=str(tmp_path / "autonomous"))
        designer.optimizer.use_real_engines = False
        designer.generate("Hunt 200", max_iterations=1)
        iters = tmp_path / "autonomous" / "autonomous_iterations.json"
        assert iters.exists()
        with open(iters, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_exports_metrics_json(self, tmp_path):
        designer = AutonomousWorldDesigner(output_dir=str(tmp_path / "autonomous"))
        designer.optimizer.use_real_engines = False
        designer.generate("Hunt 200", max_iterations=1)
        metrics = tmp_path / "autonomous" / "autonomous_metrics.json"
        assert metrics.exists()
        with open(metrics, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "final_scores" in data
        assert "convergence_data" in data

    def test_score_history_is_tracked(self, tmp_path):
        designer = AutonomousWorldDesigner(output_dir=str(tmp_path / "autonomous"))
        designer.optimizer.use_real_engines = False
        designer.generate("Hunt 200", max_iterations=3)
        stats = designer.optimizer.get_optimization_stats()
        assert "score_history" in stats
        assert len(stats["score_history"]) >= 1

    def test_to_dict_from_dict_roundtrip(self, tmp_path):
        designer = AutonomousWorldDesigner(output_dir=str(tmp_path / "autonomous"))
        designer.optimizer.use_real_engines = False
        designer.generate("Hunt 200", max_iterations=1)
        data = designer.to_dict()
        restored = AutonomousWorldDesigner.from_dict(data)
        assert len(restored.history) == len(designer.history)
