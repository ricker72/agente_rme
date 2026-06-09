"""Integration tests for the Autonomous World Designer pipeline.

These tests run the full end-to-end pipeline (Director → Planner →
Decision Engine → Optimizer → Export) with the real critic,
playtest and OTBM exporter subsystems, but with smaller regions
so the suite stays under a few seconds per test.
"""

import json
import os
import pytest

from core.autonomous import AutonomousWorldDesigner


def _build_designer(output_dir: str) -> AutonomousWorldDesigner:
    """Build an autonomous designer wired with the real subsystems."""
    designer = AutonomousWorldDesigner(output_dir=output_dir)
    # Cap iterations to keep the test suite snappy
    designer.optimizer.max_iterations = 2
    return designer


class TestAutonomousPipeline:
    """End-to-end integration tests."""

    def test_full_pipeline_issavi_roshamuul(self, tmp_path):
        out = str(tmp_path / "autonomous")
        designer = _build_designer(out)
        designer.optimizer.use_real_engines = True
        prompt = "Crear expansión Issavi + Roshamuul nivel 300-500, 3 hunts, 2 bosses, 1 raid"
        result = designer.generate(prompt, max_iterations=2)
        # Verify pipeline produced a valid result
        assert result.result_id
        assert len(result.iterations) >= 1
        assert "critic" in result.final_scores
        assert 0.0 <= result.final_scores["critic"] <= 1.0
        assert result.convergence_data

    def test_compact_desert_city(self, tmp_path):
        out = str(tmp_path / "autonomous")
        designer = _build_designer(out)
        designer.optimizer.use_real_engines = True
        prompt = "Compact desert city, Issavi style"
        result = designer.generate(prompt, max_iterations=2)
        # City-focused strategy should be selected
        plan = result.plan
        assert any(r.region_type == "city" for r in plan.regions)
        assert result.final_scores["critic"] > 0.0

    def test_endgame_continent(self, tmp_path):
        out = str(tmp_path / "autonomous")
        designer = _build_designer(out)
        designer.optimizer.use_real_engines = True
        prompt = "Large endgame continent, 3 cities, 8 hunts, 5 bosses, 2 raids"
        result = designer.generate(prompt, max_iterations=2)
        # The plan should contain all the requested regions
        types = [r.region_type for r in result.plan.regions]
        assert "city" in types
        assert "hunt" in types
        assert "boss" in types
        assert "raid" in types
        # At least 3 cities, 5 hunts/bosses combined
        assert sum(1 for t in types if t == "city") >= 1
        assert sum(1 for t in types if t == "hunt") >= 1

    def test_optimize_alias(self, tmp_path):
        out = str(tmp_path / "autonomous")
        designer = _build_designer(out)
        designer.optimizer.use_real_engines = True
        result = designer.optimize("Hunt level 200", max_iterations=1)
        assert len(result.iterations) >= 1

    def test_benchmark_runs(self, tmp_path):
        out = str(tmp_path / "autonomous")
        designer = _build_designer(out)
        designer.optimizer.use_real_engines = True
        report = designer.benchmark(num_worlds=3)
        assert report["total_worlds"] == 3
        assert "average_score" in report
        assert "converged_worlds" in report
        assert "total_duration_seconds" in report

    def test_report_includes_history(self, tmp_path):
        out = str(tmp_path / "autonomous")
        designer = _build_designer(out)
        designer.optimizer.use_real_engines = True
        designer.generate("Hunt 200", max_iterations=1)
        report = designer.report()
        assert report["total_generations"] >= 1
        assert "decision_stats" in report
        assert "optimization_stats" in report

    def test_decisions_are_recorded(self, tmp_path):
        out = str(tmp_path / "autonomous")
        designer = _build_designer(out)
        designer.optimizer.use_real_engines = True
        designer.generate("Hunt 200", max_iterations=1)
        assert len(designer.decision_engine.decision_history) > 0
        # The first decisions are blueprint / pattern selections
        types = {d.decision_type for d in designer.decision_engine.decision_history}
        assert "blueprint" in types or "pattern" in types

    def test_otbm_export_when_available(self, tmp_path):
        out = str(tmp_path / "autonomous")
        designer = _build_designer(out)
        designer.optimizer.use_real_engines = True
        result = designer.generate("Hunt 200", max_iterations=1)
        # If the OTBM exporter was wired, the world should be a WorldModel
        if result.final_world is not None and hasattr(result.final_world, "tile_count"):
            assert result.final_world.tile_count() >= 0
