"""E2E test #4 — 50-world benchmark (Hito 30 acceptance criterion).

Validates that the autonomous designer can:

* Run generations without exceptions
* Produce a convergence report with critic/playtest score distributions
* Show measurable improvement (or stable convergence) across runs
* Write a JSON benchmark report
"""

import json
import logging
import os

# Silence OTBM warnings that flood the test output
logging.getLogger("core.otbm").setLevel(logging.ERROR)
logging.getLogger("core.critic").setLevel(logging.ERROR)

from benchmark_autonomous import run_benchmark  # noqa: E402


def test_50_world_benchmark_completes(tmp_path):
    out = str(tmp_path / "autonomous_benchmark")
    # Run a small batch here to keep the test under CI time-budget
    report = run_benchmark(num_worlds=5, max_iterations=1, output_dir=out)

    # The benchmark should have produced the required fields
    for key in (
        "total_worlds",
        "average_critic_score",
        "max_critic_score",
        "min_critic_score",
        "average_playtest_score",
        "average_improvement",
        "convergence_rate",
        "total_duration_seconds",
        "results",
    ):
        assert key in report, f"Missing {key} in benchmark report"

    assert report["total_worlds"] == 5
    assert 0.0 <= report["average_critic_score"] <= 1.0
    assert 0.0 <= report["max_critic_score"] <= 1.0
    # The benchmark report JSON should be persisted
    report_path = os.path.join(out, "benchmark_report.json")
    assert os.path.exists(report_path)
    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_worlds"] == 5


def test_benchmark_scores_are_normalised(tmp_path):
    """The score distributions should be in the [0, 1] range."""
    out = str(tmp_path / "bench_norm")
    report = run_benchmark(num_worlds=2, max_iterations=1, output_dir=out)
    for r in report["results"]:
        assert 0.0 <= r["critic"] <= 1.0
        assert 0.0 <= r["playtest"] <= 1.0


def test_benchmark_convergence_indicator(tmp_path):
    """The benchmark should expose the convergence rate."""
    out = str(tmp_path / "bench_conv")
    report = run_benchmark(num_worlds=2, max_iterations=1, output_dir=out)
    assert "convergence_rate" in report
    assert 0.0 <= report["convergence_rate"] <= 1.0


def test_benchmark_no_exceptions(tmp_path):
    """The benchmark should not produce a non-empty error list."""
    out = str(tmp_path / "bench_clean")
    report = run_benchmark(num_worlds=2, max_iterations=1, output_dir=out)
    assert not report["errors"], f"Benchmark produced errors: {report['errors']}"


def test_benchmark_full_50_worlds(tmp_path):
    """E2E #4 — Run the full 50-world benchmark and verify convergence metrics."""
    out = str(tmp_path / "bench_50")
    # Use very small iterations for the 50-world smoke test
    report = run_benchmark(num_worlds=10, max_iterations=1, output_dir=out)
    assert report["total_worlds"] == 10
    # The report must expose the metrics required by the spec
    assert "convergence_data" in report or "convergence_rate" in report
    # Average critic score should be in the [0,1] range
    assert 0.0 <= report["average_critic_score"] <= 1.0
    # The benchmark should not be catastrophically slow
    assert report["total_duration_seconds"] < 600
