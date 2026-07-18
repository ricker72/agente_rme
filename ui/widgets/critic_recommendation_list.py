"""Recommendation list for Visual Critic Studio."""

from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QListWidget, QVBoxLayout, QWidget


class CriticRecommendationList(QGroupBox):
    """Render critic recommendations."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Recommendations", parent)
        self.list_widget = QListWidget(self)
        self._build_ui()

    def update_recommendations(self, recommendations: list[str]) -> None:
        """Update recommendation rows."""
        self.list_widget.clear()
        if not recommendations:
            self.list_widget.addItem("No recommendations")
            return
        for index, recommendation in enumerate(recommendations, start=1):
            priority = "HIGH" if index == 1 else "MEDIUM"
            self.list_widget.addItem(
                f"{priority} | Action: {recommendation} | Reason: Critic finding | "
                "Target Region: -"
            )

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
        self.update_recommendations([])
