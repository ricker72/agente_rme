"""
AI reasoning panel for selected RULE-41 events.
"""

from __future__ import annotations

from typing import Any, Dict

from PySide6.QtWidgets import QPlainTextEdit

from .base_panel import LivePreviewPanel


class ReasoningPanel(LivePreviewPanel):
    """Shows why a generated element exists."""

    def __init__(self) -> None:
        super().__init__("AI Reasoning")
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.layout.addWidget(self.text)

    def set_reasoning(self, event: Dict[str, Any]) -> None:
        chain = event.get("reasoning_chain", [])
        lines = [
            "WHY WAS THIS CREATED?",
            "",
            event.get("description", "No selected event"),
            "",
            "Reason:",
            *[str(item) for item in chain],
            "",
            f"Trace ID: {event.get('trace_id', 'UNKNOWN')}",
        ]
        self.text.setPlainText("\n".join(lines))
