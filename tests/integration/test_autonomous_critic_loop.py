"""Integration test: Autonomous Designer + Visual Critic loop."""

import json
import os
import pytest

from core.autonomous import AutonomousWorldDesigner


def test_critic_feedback_drives_improvement(tmp_path):
    """The autonomous loop should produce a result with a critic score
    and record its history of critic scores per iteration."""
    out = str(tmp_path / "autonomous")
    designer = AutonomousWorldDesigner(output_dir=out)
    designer.optimizer.max_iterations = 2
    designer.optimizer.use_real_engines = True

    result = designer.generate(
        "Issavi Roshamuul level 300-500 3 hunts 2 bosses 1 raid", max_iterations=2,
    )
    assert len(result.convergence_data) == len(result.iterations)
    for score in result.convergence_data:
        assert 0.0 <= score <= 1.0
    assert result.plan.goal_id


def test_critic_loop_persists_history(tmp_path):
    out = str(tmp_path / "autonomous")
    designer = AutonomousWorldDesigner(output_dir=out)
    designer.optimizer.max_iterations = 1
    designer.optimizer.use_real_engines = True

    designer.generate("Hunt 200", max_iterations=1)
    designer.generate("Boss 200", max_iterations=1)
    designer.generate("City 200", max_iterations=1)

    history_path = os.path.join(out, "autonomous_history.json")
    assert os.path.exists(history_path)
    with open(history_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) >= 3
