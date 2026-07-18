"""Search panel for the Knowledge Explorer."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget


class KnowledgeSearchPanel(QWidget):
    """Collect knowledge search text and expose search actions."""

    EXAMPLES = [
        "Issavi Hunt",
        "Roshamuul Boss",
        "Soul War Region",
        "Falcon City",
        "Library Spawn",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.query_edit = QLineEdit(self)
        self.example_combo = QComboBox(self)
        self.search_button = QPushButton("Search", self)
        self.clear_button = QPushButton("Clear", self)
        self._build_ui()

    def query_text(self) -> str:
        """Return current query text."""
        return self.query_edit.text().strip()

    def clear(self) -> None:
        """Clear the query field."""
        self.query_edit.clear()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self.query_edit.setPlaceholderText("Search knowledge entries...")
        self.example_combo.addItem("Examples")
        self.example_combo.addItems(self.EXAMPLES)
        self.example_combo.currentTextChanged.connect(self._apply_example)
        row.addWidget(self.query_edit, 1)
        row.addWidget(self.search_button)
        row.addWidget(self.clear_button)
        layout.addLayout(row)
        layout.addWidget(self.example_combo)
        self.clear_button.clicked.connect(self.clear)

    def _apply_example(self, text: str) -> None:
        if text in self.EXAMPLES:
            self.query_edit.setText(text)
