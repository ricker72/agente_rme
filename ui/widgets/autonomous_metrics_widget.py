"""Metrics widget for Autonomous Designer Workspace."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QWidget

from ui.models.autonomous_dto import AutonomousMetricsDTO


class AutonomousMetricsWidget(QGroupBox):
    """Render autonomous run metrics."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Live Metrics", parent)
        self.current_iteration_value = QLabel("0", self)
        self.best_score_value = QLabel("0.0", self)
        self.current_score_value = QLabel("0.0", self)
        self.target_score_value = QLabel("90", self)
        self.improvement_value = QLabel("0%", self)
        self.convergence_value = QLabel("Idle", self)
        self.success_value = QLabel("No", self)
        self._build_ui()

    def update_metrics(self, metrics: AutonomousMetricsDTO, target_score: int = 90) -> None:
        """Update labels from metrics DTO."""
        current = metrics.total_iterations
        successes = metrics.successful_runs
        best_score = min(100.0, successes * 10.0)
        current_score = best_score if metrics.success else 0.0
        improvement = 0 if target_score <= 0 else int((current_score / target_score) * 100)
        self.current_iteration_value.setText(str(current))
        self.best_score_value.setText(f"{best_score:.1f}")
        self.current_score_value.setText(f"{current_score:.1f}")
        self.target_score_value.setText(str(target_score))
        self.improvement_value.setText(f"{improvement}%")
        self.convergence_value.setText(metrics.status)
        self.success_value.setText("Yes" if metrics.success else "No")

    def _build_ui(self) -> None:
        layout = QFormLayout(self)
        layout.addRow("Current Iteration", self.current_iteration_value)
        layout.addRow("Best Score", self.best_score_value)
        layout.addRow("Current Score", self.current_score_value)
        layout.addRow("Target Score", self.target_score_value)
        layout.addRow("Improvement %", self.improvement_value)
        layout.addRow("Convergence Status", self.convergence_value)
        layout.addRow("Success State", self.success_value)
