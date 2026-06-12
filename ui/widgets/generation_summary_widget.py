"""Generation summary widget."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QWidget

from ui.models.world_dto import WorldDTO


class GenerationSummaryWidget(QGroupBox):
    """Display the latest world generation summary."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Summary", parent)
        self.name_value = QLabel("-", self)
        self.theme_value = QLabel("-", self)
        self.level_range_value = QLabel("-", self)
        self.tile_count_value = QLabel("0", self)
        self.status_value = QLabel("Idle", self)
        self.duration_value = QLabel("-", self)
        self._build_ui()

    def update_summary(
        self,
        world: WorldDTO,
        theme: str,
        level_range: str,
        duration_seconds: float,
    ) -> None:
        """Update display from a world DTO."""
        self.name_value.setText(world.name or world.world_id or "-")
        self.theme_value.setText(theme)
        self.level_range_value.setText(level_range)
        self.tile_count_value.setText(self._tile_count_from_description(world.description))
        self.status_value.setText(world.status)
        self.duration_value.setText(f"{duration_seconds:.2f}s")

    def _build_ui(self) -> None:
        layout = QFormLayout(self)
        layout.addRow("World Name", self.name_value)
        layout.addRow("Theme", self.theme_value)
        layout.addRow("Level Range", self.level_range_value)
        layout.addRow("Tile Count", self.tile_count_value)
        layout.addRow("Status", self.status_value)
        layout.addRow("Generation Time", self.duration_value)

    @staticmethod
    def _tile_count_from_description(description: str) -> str:
        first = description.split(" ", 1)[0]
        return first if first.isdigit() else "0"
