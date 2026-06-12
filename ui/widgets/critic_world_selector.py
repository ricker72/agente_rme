"""World/report selector for Visual Critic Studio."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QLineEdit, QWidget


class CriticWorldSelector(QGroupBox):
    """Collect world and report selection values."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("World / Report Selection", parent)
        self.world_id_edit = QLineEdit(self)
        self.profile_combo = QComboBox(self)
        self._build_ui()

    def world_id(self) -> str:
        """Return selected world id."""
        return self.world_id_edit.text().strip() or "current-world"

    def analysis_profile(self) -> str:
        """Return selected analysis profile."""
        return self.profile_combo.currentText()

    def _build_ui(self) -> None:
        layout = QFormLayout(self)
        self.world_id_edit.setPlaceholderText("current-world")
        self.profile_combo.addItems(["default", "visual", "navigation", "full"])
        layout.addRow("World", self.world_id_edit)
        layout.addRow("Report Profile", self.profile_combo)
