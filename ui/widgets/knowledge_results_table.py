"""Results table for Knowledge Explorer."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QWidget

from ui.models.knowledge_dto import KnowledgeResultDTO


class KnowledgeResultsTable(QTableWidget):
    """Sortable selectable table of knowledge results."""

    result_selected = Signal(object)

    HEADERS = ["Name", "Type", "Level Range", "Quality Score", "Similarity Score", "Source"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(0, len(self.HEADERS), parent)
        self._results: list[KnowledgeResultDTO] = []
        self._build_ui()

    def update_results(self, results: list[KnowledgeResultDTO]) -> None:
        """Render result DTOs."""
        self.setSortingEnabled(False)
        self._results = list(results)
        self.setRowCount(len(results))
        for row, result in enumerate(results):
            values = [
                result.title,
                result.entry_type,
                self._level_range(result),
                self._quality(result),
                f"{result.relevance:.2f}",
                result.source,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, result)
                self.setItem(row, col, item)
        self.setSortingEnabled(True)

    def selected_result(self) -> KnowledgeResultDTO | None:
        """Return the currently selected DTO."""
        row = self.currentRow()
        if row < 0 or row >= len(self._results):
            return None
        return self._results[row]

    def _build_ui(self) -> None:
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.itemSelectionChanged.connect(self._emit_selection)

    def _emit_selection(self) -> None:
        result = self.selected_result()
        if result is not None:
            self.result_selected.emit(result)

    @staticmethod
    def _level_range(result: KnowledgeResultDTO) -> str:
        for tag in result.tags:
            if tag.lower().startswith("level:"):
                return tag.split(":", 1)[1]
        return "-"

    @staticmethod
    def _quality(result: KnowledgeResultDTO) -> str:
        return f"{min(100.0, max(0.0, result.relevance * 100.0)):.1f}"
