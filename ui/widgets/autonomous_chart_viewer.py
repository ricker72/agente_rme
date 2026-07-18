"""Chart viewer for Autonomous Designer Workspace."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QTabWidget, QVBoxLayout, QWidget


class AutonomousChartViewer(QTabWidget):
    """Display optimization charts with safe fallbacks."""

    CHARTS = {
        "Iteration Scores": "iteration_scores.png",
        "Critic Progress": "critic_progress.png",
        "Optimization Curve": "optimization_curve.png",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.labels: dict[str, QLabel] = {}
        self._build_ui()

    def refresh_charts(self) -> None:
        """Load known chart PNGs when present."""
        for title, path in self.CHARTS.items():
            self._load_chart(title, path)

    def _build_ui(self) -> None:
        for title in self.CHARTS:
            page = QWidget(self)
            layout = QVBoxLayout(page)
            label = QLabel("No chart available", page)
            label.setMinimumHeight(160)
            label.setWordWrap(True)
            layout.addWidget(label)
            self.labels[title] = label
            self.addTab(page, title)

    def _load_chart(self, title: str, path: str) -> bool:
        label = self.labels[title]
        candidate = Path(path)
        if not candidate.is_file():
            label.setPixmap(QPixmap())
            label.setText("No chart available")
            return False
        pixmap = QPixmap(str(candidate))
        if pixmap.isNull():
            label.setPixmap(QPixmap())
            label.setText("No chart available")
            return False
        label.setPixmap(pixmap.scaledToWidth(420))
        label.setText("")
        return True
