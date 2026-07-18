"""Goal panel for Autonomous Designer Workspace."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QPlainTextEdit, QSpinBox, QWidget


@dataclass(slots=True)
class AutonomousGoalSettings:
    """Goal settings collected from the UI."""

    prompt: str
    target_score: int
    max_iterations: int


class AutonomousGoalPanel(QGroupBox):
    """Collect autonomous design goal and run targets."""

    EXAMPLES = [
        "Create an Issavi + Roshamuul expansion for levels 300-500",
        "Generate a compact desert city in Issavi style",
        "Create a large endgame continent with 3 cities, 8 hunts, and 5 bosses",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Goal", parent)
        self.example_combo = QComboBox(self)
        self.prompt_edit = QPlainTextEdit(self)
        self.target_score_spin = QSpinBox(self)
        self.max_iterations_spin = QSpinBox(self)
        self._build_ui()

    def settings(self) -> AutonomousGoalSettings:
        """Return current goal settings."""
        return AutonomousGoalSettings(
            prompt=self.prompt_edit.toPlainText().strip(),
            target_score=self.target_score_spin.value(),
            max_iterations=self.max_iterations_spin.value(),
        )

    def is_valid(self) -> bool:
        """Return True when a goal prompt is usable."""
        return len(self.settings().prompt) >= 10

    def set_prompt(self, text: str) -> None:
        """Set prompt text."""
        self.prompt_edit.setPlainText(text)

    def _build_ui(self) -> None:
        layout = QFormLayout(self)
        self.example_combo.addItem("Examples")
        self.example_combo.addItems(self.EXAMPLES)
        self.example_combo.currentTextChanged.connect(self._apply_example)
        self.prompt_edit.setMinimumHeight(100)
        self.prompt_edit.setPlaceholderText("Describe the autonomous design goal...")
        self.target_score_spin.setRange(1, 100)
        self.target_score_spin.setValue(90)
        self.max_iterations_spin.setRange(1, 200)
        self.max_iterations_spin.setValue(20)
        layout.addRow("Examples", self.example_combo)
        layout.addRow("Prompt", self.prompt_edit)
        layout.addRow("Target Critic Score", self.target_score_spin)
        layout.addRow("Max Iterations", self.max_iterations_spin)

    def _apply_example(self, text: str) -> None:
        if text in self.EXAMPLES:
            self.set_prompt(text)
