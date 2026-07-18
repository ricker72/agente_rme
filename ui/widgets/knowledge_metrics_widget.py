"""Metrics panel for Knowledge Explorer."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QWidget

from ui.models.knowledge_dto import KnowledgeMetricsDTO


class KnowledgeMetricsWidget(QGroupBox):
    """Render knowledge dataset metrics."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Metrics", parent)
        self.dataset_entries_value = QLabel("0", self)
        self.cities_value = QLabel("0", self)
        self.hunts_value = QLabel("0", self)
        self.bosses_value = QLabel("0", self)
        self.raids_value = QLabel("0", self)
        self.quests_value = QLabel("0", self)
        self.regions_value = QLabel("0", self)
        self.biomes_value = QLabel("0", self)
        self.coverage_value = QLabel("0%", self)
        self.status_value = QLabel("Idle", self)
        self._build_ui()

    def update_metrics(self, metrics: KnowledgeMetricsDTO) -> None:
        """Update metrics labels."""
        total = metrics.total_entries
        self.dataset_entries_value.setText(str(total))
        self.cities_value.setText("0")
        self.hunts_value.setText("0")
        self.bosses_value.setText("0")
        self.raids_value.setText("0")
        self.quests_value.setText("0")
        self.regions_value.setText("0")
        self.biomes_value.setText("0")
        coverage = 100 if metrics.success and total > 0 else 0
        self.coverage_value.setText(f"{coverage}%")
        self.status_value.setText(metrics.status)

    def _build_ui(self) -> None:
        layout = QFormLayout(self)
        layout.addRow("Dataset Entries", self.dataset_entries_value)
        layout.addRow("Cities", self.cities_value)
        layout.addRow("Hunts", self.hunts_value)
        layout.addRow("Bosses", self.bosses_value)
        layout.addRow("Raids", self.raids_value)
        layout.addRow("Quests", self.quests_value)
        layout.addRow("Regions", self.regions_value)
        layout.addRow("Biomes", self.biomes_value)
        layout.addRow("Coverage %", self.coverage_value)
        layout.addRow("Status", self.status_value)
