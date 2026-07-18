"""
Live generation trace panel consuming RULE-41 artifacts.
"""

from __future__ import annotations

from typing import Any, Dict, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget

from .base_panel import LivePreviewPanel


class GenerationTraceWidget(LivePreviewPanel):
    """Displays real-time generation progress messages."""

    mandatory_messages = [
        "Generating Temple District...",
        "Generating Depot...",
        "Generating Roads...",
        "Applying Brush Intelligence...",
        "Applying Appearance Selection...",
        "Generating Houses...",
        "Generating Shops...",
        "Generating NPCs...",
        "Generating Spawns...",
        "Generating Quests...",
        "Validating Connectivity...",
        "Validating Accessibility...",
        "Validating Floors...",
        "Validating Hunts...",
        "Export Validation...",
    ]

    def __init__(self) -> None:
        super().__init__("Live Generation Trace")
        self.list_widget = QListWidget()
        self.list_widget.setWordWrap(True)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.layout.addWidget(self.list_widget)

    def set_events(self, events: List[Dict[str, Any]]) -> None:
        self.list_widget.clear()
        descriptions = [event.get("description", "") for event in events]
        for message in self.mandatory_messages:
            state = "PASS" if message in descriptions else "WAITING"
            self.list_widget.addItem(f"{state} - {message}")
