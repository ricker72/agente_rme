"""
Recent Artifacts Widget for Agente RME Studio Dashboard.
Displays a table of recent artifacts from the output directory.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class RecentArtifactsWidget(QFrame):
    """Widget displaying recent artifacts in a table."""

    STYLESHEET = """
        QFrame {
            background-color: #1e1e2e;
            border-radius: 8px;
            border: 1px solid #313244;
            padding: 16px;
        }
        QTableWidget {
            background-color: #181825;
            border: none;
            border-radius: 4px;
            gridline-color: #313244;
            color: #cdd6f4;
            font-size: 12px;
        }
        QTableWidget::item {
            padding: 6px 8px;
        }
        QTableWidget::item:selected {
            background-color: #45475a;
        }
        QHeaderView::section {
            background-color: #11111b;
            color: #a6adc8;
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
            padding: 6px 8px;
            border: none;
            border-bottom: 1px solid #313244;
        }
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("recent_artifacts_widget")
        self.setStyleSheet(self.STYLESHEET)
        self.setFixedHeight(280)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        title_label = QLabel("Recent Artifacts", self)
        title_label.setStyleSheet(
            "color: #a6adc8; font-size: 12px; font-weight: 600; text-transform: uppercase;"
        )
        layout.addWidget(title_label)

        self._table = QTableWidget(self)
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Name", "Date", "Size"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

    def update_artifacts(self, artifacts):
        self._table.setRowCount(len(artifacts))
        for i, artifact in enumerate(artifacts):
            self._table.setItem(i, 0, QTableWidgetItem(artifact.name))
            self._table.setItem(i, 1, QTableWidgetItem(artifact.modified))
            self._table.setItem(i, 2, QTableWidgetItem(artifact.size))
