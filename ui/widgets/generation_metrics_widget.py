"""Generation metrics widget."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QWidget

from ui.models.world_dto import WorldDTO


@dataclass(slots=True)
class GenerationMetrics:
    """Metrics displayed after generation."""

    duration_seconds: float = 0.0
    success: bool = False
    generated_regions: int = 0
    generated_hunts: int = 0
    generated_cities: int = 0


class GenerationMetricsWidget(QGroupBox):
    """Render generated world metrics."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Metrics", parent)
        self.duration_value = QLabel("0.00s", self)
        self.success_value = QLabel("No", self)
        self.regions_value = QLabel("0", self)
        self.hunts_value = QLabel("0", self)
        self.cities_value = QLabel("0", self)
        self._build_ui()

    def update_metrics(self, metrics: GenerationMetrics) -> None:
        """Update labels from metrics."""
        self.duration_value.setText(f"{metrics.duration_seconds:.2f}s")
        self.success_value.setText("Yes" if metrics.success else "No")
        self.regions_value.setText(str(metrics.generated_regions))
        self.hunts_value.setText(str(metrics.generated_hunts))
        self.cities_value.setText(str(metrics.generated_cities))

    def build_metrics(self, world: WorldDTO, duration_seconds: float, mode: str) -> GenerationMetrics:
        """Build display metrics from a DTO and mode."""
        regions = max(1, world.width // 128) if world.success else 0
        return GenerationMetrics(
            duration_seconds=duration_seconds,
            success=world.success,
            generated_regions=regions,
            generated_hunts=1 if world.success else 0,
            generated_cities=1 if world.success and mode == "Expansion" else 0,
        )

    def _build_ui(self) -> None:
        layout = QFormLayout(self)
        layout.addRow("Generation Duration", self.duration_value)
        layout.addRow("Success State", self.success_value)
        layout.addRow("Generated Regions", self.regions_value)
        layout.addRow("Generated Hunts", self.hunts_value)
        layout.addRow("Generated Cities", self.cities_value)
