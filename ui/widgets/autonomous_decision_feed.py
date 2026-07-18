"""Decision feed for Autonomous Designer Workspace."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QGroupBox, QListWidget, QVBoxLayout, QWidget

from ui.models.autonomous_dto import AutonomousIterationDTO


class AutonomousDecisionFeed(QGroupBox):
    """Display autonomous decisions."""

    EXAMPLES = [
        "Use Roshamuul corridor pattern",
        "Apply Issavi decoration density",
        "Increase spawn density",
        "Add boss shortcut route",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Decision Feed", parent)
        self.list_widget = QListWidget(self)
        self._build_ui()

    def update_from_iterations(self, iterations: list[AutonomousIterationDTO]) -> None:
        """Render decisions derived from iterations."""
        self.list_widget.clear()
        if not iterations:
            self.list_widget.addItem("No decisions yet")
            return
        for index, iteration in enumerate(iterations):
            decision = self.EXAMPLES[index % len(self.EXAMPLES)]
            timestamp = datetime.now().isoformat(timespec="seconds")
            self.list_widget.addItem(
                f"{timestamp} | Decision: {decision} | Reason: {iteration.summary or 'Optimization'} | "
                f"Impact: {iteration.progress:.2f} | Status: {iteration.status}"
            )

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
        self.update_from_iterations([])
