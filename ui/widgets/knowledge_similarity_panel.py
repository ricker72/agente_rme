"""Similarity panel for Knowledge Explorer."""

from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from ui.models.knowledge_dto import KnowledgeResultDTO


class KnowledgeSimilarityPanel(QGroupBox):
    """Render similar knowledge entries."""

    HEADERS = ["Name", "Similarity", "Type", "Quality"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Similarity", parent)
        self.find_button = QPushButton("Find Similar", self)
        self.table = QTableWidget(0, len(self.HEADERS), self)
        self._build_ui()

    def update_results(self, results: list[KnowledgeResultDTO]) -> None:
        """Render similar entry DTOs."""
        self.table.setRowCount(len(results))
        for row, result in enumerate(results):
            values = [
                result.title,
                f"{result.relevance:.2f}",
                result.entry_type,
                f"{result.relevance * 100.0:.1f}",
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        layout.addWidget(self.find_button)
        layout.addWidget(self.table)
