"""Status widget for Autonomous Designer Workspace."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QWidget


class AutonomousStatusWidget(QGroupBox):
    """Current autonomous design status."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Current Status", parent)
        self.state_value = QLabel("Idle", self)
        self.summary_value = QLabel("-", self)
        self._build_ui()

    def update_status(self, state: str, summary: str = "") -> None:
        """Update status labels."""
        self.state_value.setText(state)
        self.summary_value.setText(summary or "-")

    def _build_ui(self) -> None:
        layout = QFormLayout(self)
        layout.addRow("State", self.state_value)
        layout.addRow("Summary", self.summary_value)
