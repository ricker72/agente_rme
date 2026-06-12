"""Recommendation panel for Knowledge Explorer."""

from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QListWidget, QVBoxLayout, QWidget

from ui.models.knowledge_dto import KnowledgeResultDTO


class KnowledgeRecommendationPanel(QGroupBox):
    """Display reusable knowledge recommendations."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Recommendations", parent)
        self.list_widget = QListWidget(self)
        self._build_ui()

    def update_recommendations(self, results: list[KnowledgeResultDTO]) -> None:
        """Build recommendations from search results."""
        self.list_widget.clear()
        if not results:
            self.list_widget.addItem("No recommendations")
            return
        for result in results[:5]:
            noun = result.title or result.entry_type or "Knowledge Entry"
            kind = result.entry_type.title() or "Pattern"
            self.list_widget.addItem(f"Reuse {noun} {kind} Strategy")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
        self.update_recommendations([])
