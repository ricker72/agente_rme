"""Additional tests for the AutonomousWorldDesigner to lift coverage."""

import os
from unittest.mock import MagicMock

from core.autonomous import AutonomousWorldDesigner


class TestAutonomousWorldDesignerExtra:
    """Extra tests targeting uncovered code in AutonomousWorldDesigner."""

    def test_post_init_creates_output_dir(self, tmp_path):
        out = str(tmp_path / "awd")
        AutonomousWorldDesigner(output_dir=out)
        assert os.path.isdir(out)

    def test_post_init_shares_director_with_planner(self, tmp_path):
        out = str(tmp_path / "awd")
        designer = AutonomousWorldDesigner(output_dir=out)
        # Planner should share the same director instance
        assert designer.planner.director is designer.director

    def test_wire_subsystems_sets_engines(self, tmp_path):
        out = str(tmp_path / "awd")

        class FakeKE:
            def find_similar_hunts(self, name, k=5):
                return []

        class FakeBI:
            def recommend(self, t, top_k=5):
                return []

        designer = AutonomousWorldDesigner(output_dir=out)
        designer.wire_subsystems(
            knowledge_engine=FakeKE(),
            blueprint_intelligence=FakeBI(),
        )
        assert designer.knowledge_engine is not None
        assert designer.blueprint_intelligence is not None
        assert designer.director.knowledge_engine is not None
        assert designer.director.blueprint_intelligence is not None
        assert designer.decision_engine.knowledge_engine is not None
        assert designer.decision_engine.blueprint_intelligence is not None

    def test_wire_visual_critic_to_optimizer(self, tmp_path):
        out = str(tmp_path / "awd")

        class FakeCritic:
            def analyze(self, w):
                r = MagicMock()
                r.overall_score = 80
                return r

        designer = AutonomousWorldDesigner(output_dir=out)
        designer.wire_subsystems(visual_critic=FakeCritic())
        assert designer.optimizer.visual_critic is not None

    def test_generate_records_history(self, tmp_path):
        out = str(tmp_path / "awd")
        designer = AutonomousWorldDesigner(output_dir=out)
        designer.optimizer.use_real_engines = False
        designer.optimizer.max_iterations = 1
        designer.generate("Hunt 200", max_iterations=1)
        assert len(designer.history) == 1
        assert "timestamp" in designer.history[0]

    def test_generate_exports_all_artifacts(self, tmp_path):
        out = str(tmp_path / "awd")
        designer = AutonomousWorldDesigner(output_dir=out)
        designer.optimizer.use_real_engines = False
        designer.optimizer.max_iterations = 1
        designer.generate("Hunt 200", max_iterations=1)
        for filename in (
            "autonomous_history.json",
            "autonomous_decisions.json",
            "autonomous_iterations.json",
            "autonomous_metrics.json",
        ):
            assert os.path.exists(os.path.join(out, filename)), filename

    def test_benchmark_returns_full_report(self, tmp_path):
        out = str(tmp_path / "awd")
        designer = AutonomousWorldDesigner(output_dir=out)
        designer.optimizer.use_real_engines = False
        report = designer.benchmark(num_worlds=2)
        for key in (
            "total_worlds",
            "successful_worlds",
            "average_score",
            "max_score",
            "min_score",
            "converged_worlds",
            "total_duration_seconds",
            "average_improvement",
        ):
            assert key in report, f"Missing {key}"

    def test_to_dict_from_dict_roundtrip(self, tmp_path):
        out = str(tmp_path / "awd")
        designer = AutonomousWorldDesigner(output_dir=out)
        designer.optimizer.use_real_engines = False
        designer.generate("Hunt 200", max_iterations=1)
        data = designer.to_dict()
        restored = AutonomousWorldDesigner.from_dict(data)
        assert len(restored.history) == len(designer.history)
        assert restored.output_dir == designer.output_dir

    def test_report_returns_history_and_stats(self, tmp_path):
        out = str(tmp_path / "awd")
        designer = AutonomousWorldDesigner(output_dir=out)
        designer.optimizer.use_real_engines = False
        designer.generate("Hunt 200", max_iterations=1)
        r = designer.report()
        assert "total_generations" in r
        assert "history" in r
        assert "decision_stats" in r
        assert "optimization_stats" in r
        assert "memory_stats" in r
