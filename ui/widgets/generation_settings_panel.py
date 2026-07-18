"""Generation settings panel for the World Generation Studio."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QWidget,
)


@dataclass(slots=True)
class GenerationSettings:
    """UI settings used to build a world generation request."""

    size: str
    theme: str
    min_level: int
    max_level: int
    mode: str


class GenerationSettingsPanel(QGroupBox):
    """Collect generation size, theme, levels, and mode."""

    SIZE_DIMENSIONS = {
        "Small": (128, 128),
        "Medium": (256, 256),
        "Large": (512, 512),
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Settings", parent)
        self.size_combo = QComboBox(self)
        self.theme_combo = QComboBox(self)
        self.min_level_spin = QSpinBox(self)
        self.max_level_spin = QSpinBox(self)
        self.mode_combo = QComboBox(self)
        self._build_ui()

    def settings(self) -> GenerationSettings:
        """Return current settings as a typed object."""
        return GenerationSettings(
            size=self.size_combo.currentText(),
            theme=self.theme_combo.currentText(),
            min_level=self.min_level_spin.value(),
            max_level=self.max_level_spin.value(),
            mode=self.mode_combo.currentText(),
        )

    def dimensions(self) -> tuple[int, int]:
        """Return width and height for the selected world size."""
        return self.SIZE_DIMENSIONS.get(self.size_combo.currentText(), (256, 256))

    def is_valid(self) -> bool:
        """Return True when level range is valid."""
        return self.min_level_spin.value() <= self.max_level_spin.value()

    def _build_ui(self) -> None:
        layout = QFormLayout(self)
        layout.setSpacing(10)

        self.size_combo.addItems(["Small", "Medium", "Large"])
        self.size_combo.setCurrentText("Medium")
        layout.addRow("World Size", self.size_combo)

        self.theme_combo.addItems(["Issavi", "Roshamuul", "Soul War", "Falcon", "Custom"])
        layout.addRow("Theme", self.theme_combo)

        self.min_level_spin.setRange(1, 2000)
        self.min_level_spin.setValue(300)
        layout.addRow("Level Min", self.min_level_spin)

        self.max_level_spin.setRange(1, 2000)
        self.max_level_spin.setValue(500)
        layout.addRow("Level Max", self.max_level_spin)

        self.mode_combo.addItems(["Standard", "Expansion", "Autonomous"])
        layout.addRow("Generation Mode", self.mode_combo)
