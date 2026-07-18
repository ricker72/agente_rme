"""Iteration table for Autonomous Designer Workspace."""

from __future__ import annotations

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QWidget

from ui.models.autonomous_dto import AutonomousIterationDTO


class AutonomousIterationTable(QTableWidget):
    """Render autonomous iteration history."""

    HEADERS = ["Iteration", "Score", "Delta", "Duration", "Status", "Summary"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(0, len(self.HEADERS), parent)
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.setSortingEnabled(True)

    def update_iterations(self, iterations: list[AutonomousIterationDTO]) -> None:
        """Render iteration DTO rows."""
        self.setSortingEnabled(False)
        self.setRowCount(len(iterations))
        previous_score = 0.0
        for row, iteration in enumerate(iterations):
            score = iteration.progress * 100.0
            delta = score - previous_score
            previous_score = score
            values = [
                str(iteration.iteration_number),
                f"{score:.1f}",
                f"{delta:.1f}",
                "-",
                iteration.status,
                iteration.summary,
            ]
            for col, value in enumerate(values):
                self.setItem(row, col, QTableWidgetItem(value))
        self.setSortingEnabled(True)
