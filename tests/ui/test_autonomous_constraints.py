"""Tests for autonomous constraints panel."""

from __future__ import annotations

from ui.widgets.autonomous_constraints_panel import AutonomousConstraintsPanel


def test_constraints_defaults(qapp_instance: object) -> None:
    panel = AutonomousConstraintsPanel()
    constraints = panel.constraints()
    assert constraints.world_size == "Medium"
    assert constraints.strategy == "Balanced"
    assert constraints.use_knowledge
    assert constraints.use_blueprints
    assert constraints.use_visual_critic
    assert not constraints.use_evolution


def test_constraints_level_validation(qapp_instance: object) -> None:
    panel = AutonomousConstraintsPanel()
    panel.min_level_spin.setValue(600)
    panel.max_level_spin.setValue(300)
    assert not panel.is_valid()
