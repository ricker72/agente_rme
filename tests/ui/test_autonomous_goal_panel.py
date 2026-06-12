"""Tests for autonomous goal panel."""

from __future__ import annotations

from ui.widgets.autonomous_goal_panel import AutonomousGoalPanel


def test_goal_panel_defaults(qapp_instance: object) -> None:
    panel = AutonomousGoalPanel()
    assert panel.target_score_spin.value() == 90
    assert panel.max_iterations_spin.value() == 20
    assert not panel.is_valid()


def test_goal_panel_prompt_and_example(qapp_instance: object) -> None:
    panel = AutonomousGoalPanel()
    panel.example_combo.setCurrentText("Generate a compact desert city in Issavi style")
    assert panel.is_valid()
    assert "Issavi" in panel.settings().prompt
