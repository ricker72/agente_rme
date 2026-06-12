"""Constraints panel for Autonomous Designer Workspace."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QGroupBox, QSpinBox, QWidget


@dataclass(slots=True)
class AutonomousConstraints:
    """Autonomous design constraints."""

    world_size: str
    strategy: str
    min_level: int
    max_level: int
    use_knowledge: bool
    use_blueprints: bool
    use_visual_critic: bool
    use_evolution: bool


class AutonomousConstraintsPanel(QGroupBox):
    """Collect constraints and subsystem options."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Constraints", parent)
        self.size_combo = QComboBox(self)
        self.strategy_combo = QComboBox(self)
        self.min_level_spin = QSpinBox(self)
        self.max_level_spin = QSpinBox(self)
        self.knowledge_check = QCheckBox("Use Knowledge Engine", self)
        self.blueprint_check = QCheckBox("Use Blueprint Intelligence", self)
        self.critic_check = QCheckBox("Use Visual Critic", self)
        self.evolution_check = QCheckBox("Use Evolution Engine", self)
        self._build_ui()

    def constraints(self) -> AutonomousConstraints:
        """Return current constraints."""
        return AutonomousConstraints(
            world_size=self.size_combo.currentText(),
            strategy=self.strategy_combo.currentText(),
            min_level=self.min_level_spin.value(),
            max_level=self.max_level_spin.value(),
            use_knowledge=self.knowledge_check.isChecked(),
            use_blueprints=self.blueprint_check.isChecked(),
            use_visual_critic=self.critic_check.isChecked(),
            use_evolution=self.evolution_check.isChecked(),
        )

    def is_valid(self) -> bool:
        """Return True when level range is valid."""
        return self.min_level_spin.value() <= self.max_level_spin.value()

    def _build_ui(self) -> None:
        layout = QFormLayout(self)
        self.size_combo.addItems(["Small", "Medium", "Large"])
        self.size_combo.setCurrentText("Medium")
        self.strategy_combo.addItems(
            ["Balanced", "Hunt Focused", "City Focused", "Boss Focused", "Campaign Focused"]
        )
        self.min_level_spin.setRange(1, 2000)
        self.min_level_spin.setValue(300)
        self.max_level_spin.setRange(1, 2000)
        self.max_level_spin.setValue(500)
        self.knowledge_check.setChecked(True)
        self.blueprint_check.setChecked(True)
        self.critic_check.setChecked(True)
        self.evolution_check.setChecked(False)
        layout.addRow("World Size", self.size_combo)
        layout.addRow("Design Strategy", self.strategy_combo)
        layout.addRow("Level Min", self.min_level_spin)
        layout.addRow("Level Max", self.max_level_spin)
        layout.addRow(self.knowledge_check)
        layout.addRow(self.blueprint_check)
        layout.addRow(self.critic_check)
        layout.addRow(self.evolution_check)
