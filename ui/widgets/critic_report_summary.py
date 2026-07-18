"""Report summary widget for Visual Critic Studio."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QWidget

from ui.models.critic_dto import CriticDTO


class CriticReportSummary(QGroupBox):
    """Display aggregate critic report metadata."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Report Summary", parent)
        self.overall_score_value = QLabel("-", self)
        self.total_issues_value = QLabel("0", self)
        self.critical_issues_value = QLabel("0", self)
        self.recommendations_value = QLabel("0", self)
        self.last_analysis_value = QLabel("-", self)
        self.status_value = QLabel("Idle", self)
        self._build_ui()

    def update_report(self, report: CriticDTO) -> None:
        """Update summary from a critic report."""
        critical = sum(
            1 for issue in report.issues if issue.severity.upper() == "CRITICAL"
        )
        self.overall_score_value.setText(f"{report.score:.1f}")
        self.total_issues_value.setText(str(len(report.issues)))
        self.critical_issues_value.setText(str(critical))
        self.recommendations_value.setText(str(len(report.suggestions)))
        self.last_analysis_value.setText(datetime.now().isoformat(timespec="seconds"))
        self.status_value.setText(report.summary)

    def _build_ui(self) -> None:
        layout = QFormLayout(self)
        layout.addRow("Overall score", self.overall_score_value)
        layout.addRow("Total issues", self.total_issues_value)
        layout.addRow("Critical issues", self.critical_issues_value)
        layout.addRow("Recommendation count", self.recommendations_value)
        layout.addRow("Last analysis time", self.last_analysis_value)
        layout.addRow("Status", self.status_value)
