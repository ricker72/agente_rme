"""Filter widget for Knowledge Explorer."""

from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QGroupBox, QHBoxLayout, QWidget


class KnowledgeFiltersWidget(QGroupBox):
    """Select knowledge entry types."""

    TYPES = ["City", "Hunt", "Boss", "Raid", "Quest", "Region", "Biome", "Structure"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Filters", parent)
        self.checkboxes: dict[str, QCheckBox] = {}
        self._build_ui()

    def selected_types(self) -> list[str]:
        """Return selected type filters."""
        return [name for name, box in self.checkboxes.items() if box.isChecked()]

    def set_selected_types(self, names: list[str]) -> None:
        """Set selected filters."""
        selected = set(names)
        for name, box in self.checkboxes.items():
            box.setChecked(name in selected)

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        for name in self.TYPES:
            box = QCheckBox(name, self)
            self.checkboxes[name] = box
            layout.addWidget(box)
        layout.addStretch()
