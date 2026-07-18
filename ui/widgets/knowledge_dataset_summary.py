"""Dataset summary widget for Knowledge Explorer."""

from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QWidget

from ui.models.knowledge_dto import KnowledgeMetricsDTO


class KnowledgeDatasetSummary(QGroupBox):
    """Compact dataset summary."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Dataset Summary", parent)
        self.summary_label = QLabel("No dataset loaded", self)
        self._build_ui()

    def update_summary(self, metrics: KnowledgeMetricsDTO) -> None:
        """Update summary text."""
        self.summary_label.setText(
            f"{metrics.total_entries} entries | {metrics.indexed_sources} sources | "
            f"{metrics.status}"
        )

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)
