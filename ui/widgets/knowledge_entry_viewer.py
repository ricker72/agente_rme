"""Entry viewer for Knowledge Explorer."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QTextEdit, QWidget

from ui.models.knowledge_dto import KnowledgeResultDTO


class KnowledgeEntryViewer(QGroupBox):
    """Render a selected knowledge entry."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Knowledge Entry", parent)
        self.name_value = QLabel("-", self)
        self.type_value = QLabel("-", self)
        self.description_value = QTextEdit(self)
        self.level_range_value = QLabel("-", self)
        self.tags_value = QLabel("-", self)
        self.quality_value = QLabel("-", self)
        self.source_value = QLabel("-", self)
        self._build_ui()

    def display_entry(self, entry: KnowledgeResultDTO | None) -> None:
        """Display a DTO without exposing raw dictionaries."""
        if entry is None:
            self.name_value.setText("-")
            self.type_value.setText("-")
            self.description_value.setPlainText("")
            self.level_range_value.setText("-")
            self.tags_value.setText("-")
            self.quality_value.setText("-")
            self.source_value.setText("-")
            return
        self.name_value.setText(entry.title)
        self.type_value.setText(entry.entry_type)
        self.description_value.setPlainText(entry.excerpt)
        self.level_range_value.setText(self._level_range(entry))
        self.tags_value.setText(", ".join(entry.tags) if entry.tags else "-")
        self.quality_value.setText(f"{entry.relevance * 100.0:.1f}")
        self.source_value.setText(entry.source)

    def _build_ui(self) -> None:
        layout = QFormLayout(self)
        self.description_value.setReadOnly(True)
        self.description_value.setMinimumHeight(100)
        layout.addRow("Name", self.name_value)
        layout.addRow("Type", self.type_value)
        layout.addRow("Description", self.description_value)
        layout.addRow("Level Range", self.level_range_value)
        layout.addRow("Tags", self.tags_value)
        layout.addRow("Quality Score", self.quality_value)
        layout.addRow("Source", self.source_value)

    @staticmethod
    def _level_range(entry: KnowledgeResultDTO) -> str:
        for tag in entry.tags:
            if tag.lower().startswith("level:"):
                return tag.split(":", 1)[1]
        return "-"
