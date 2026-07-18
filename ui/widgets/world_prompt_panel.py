"""Prompt input panel for the World Generation Studio."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


class WorldPromptPanel(QGroupBox):
    """Collect and validate the generation prompt."""

    prompt_changed = Signal(str)

    EXAMPLES = [
        "Create an Issavi expansion for levels 300-500",
        "Generate a Roshamuul hunting area",
        "Create a custom city connected to a level 200 hunt",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Prompt", parent)
        self.prompt_edit = QPlainTextEdit(self)
        self.example_combo = QComboBox(self)
        self.counter_label = QLabel("0 characters", self)
        self.validation_label = QLabel("Prompt required", self)
        self._build_ui()

    def prompt(self) -> str:
        """Return the trimmed prompt text."""
        return self.prompt_edit.toPlainText().strip()

    def is_valid(self) -> bool:
        """Return True when the prompt is long enough to generate."""
        return len(self.prompt()) >= 10

    def set_prompt(self, text: str) -> None:
        """Set prompt text for tests and example selection."""
        self.prompt_edit.setPlainText(text)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        self.example_combo.addItem("Examples")
        self.example_combo.addItems(self.EXAMPLES)
        self.example_combo.currentTextChanged.connect(self._on_example_selected)
        layout.addWidget(self.example_combo)

        self.prompt_edit.setPlaceholderText("Describe the world, area, or expansion to generate...")
        self.prompt_edit.setMinimumHeight(92)
        self.prompt_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.prompt_edit)

        self.counter_label.setObjectName("promptCounter")
        self.validation_label.setObjectName("promptValidation")
        layout.addWidget(self.counter_label)
        layout.addWidget(self.validation_label)

    def _on_example_selected(self, text: str) -> None:
        if text in self.EXAMPLES:
            self.set_prompt(text)

    def _on_text_changed(self) -> None:
        text = self.prompt_edit.toPlainText()
        self.counter_label.setText(f"{len(text)} characters")
        if self.is_valid():
            self.validation_label.setText("Ready")
        else:
            self.validation_label.setText("Prompt must be at least 10 characters")
        self.prompt_changed.emit(text)
