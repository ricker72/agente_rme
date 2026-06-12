"""Tests for autonomous metrics and status widgets."""

from __future__ import annotations

from ui.models.autonomous_dto import AutonomousMetricsDTO
from ui.widgets.autonomous_metrics_widget import AutonomousMetricsWidget
from ui.widgets.autonomous_status_widget import AutonomousStatusWidget


def test_autonomous_metrics_rendering(qapp_instance: object) -> None:
    widget = AutonomousMetricsWidget()
    widget.update_metrics(
        AutonomousMetricsDTO(
            total_iterations=4,
            successful_runs=3,
            status="Converging",
            success=True,
        ),
        target_score=90,
    )
    assert widget.current_iteration_value.text() == "4"
    assert widget.best_score_value.text() == "30.0"
    assert widget.convergence_value.text() == "Converging"
    assert widget.success_value.text() == "Yes"


def test_autonomous_status_widget(qapp_instance: object) -> None:
    widget = AutonomousStatusWidget()
    widget.update_status("Running", "Optimizing")
    assert widget.state_value.text() == "Running"
    assert widget.summary_value.text() == "Optimizing"
