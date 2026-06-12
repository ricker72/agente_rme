"""Issue list for Visual Critic Studio."""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGroupBox, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from ui.models.critic_dto import CriticIssueDTO


class CriticIssueList(QGroupBox):
    """Render critic issues with severity cues."""

    SEVERITY_COLORS = {
        "INFO": "#89b4fa",
        "LOW": "#a6e3a1",
        "MEDIUM": "#f9e2af",
        "HIGH": "#fab387",
        "CRITICAL": "#f38ba8",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Issues", parent)
        self.list_widget = QListWidget(self)
        self._build_ui()

    def update_issues(self, issues: list[CriticIssueDTO]) -> None:
        """Update issue rows."""
        self.list_widget.clear()
        if not issues:
            self.list_widget.addItem("No issues")
            return
        for issue in issues:
            severity = issue.severity.upper()
            text = (
                f"{severity} | {issue.code or 'GENERAL'} | {issue.message} | "
                "Region: - | Coordinates: -"
            )
            item = QListWidgetItem(text)
            item.setForeground(QColor(self.SEVERITY_COLORS.get(severity, "#cdd6f4")))
            self.list_widget.addItem(item)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
        self.update_issues([])
