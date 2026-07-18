"""Persistent generation history widget."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QGroupBox, QListWidget, QVBoxLayout, QWidget


@dataclass(slots=True)
class GenerationHistoryEntry:
    """Recent generation history entry."""

    name: str
    theme: str
    level_range: str
    status: str
    duration_seconds: float


class GenerationHistoryWidget(QGroupBox):
    """Persist and display recent generation history."""

    MAX_ENTRIES = 20
    SETTINGS_KEY = "world_generation/history"

    def __init__(
        self,
        settings: QSettings | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("Generation History", parent)
        self.settings = settings or QSettings("AgenteRME", "Studio")
        self.list_widget = QListWidget(self)
        self.entries: list[GenerationHistoryEntry] = []
        self._build_ui()
        self.load_history()

    def add_entry(self, entry: GenerationHistoryEntry) -> None:
        """Add and persist a history entry."""
        self.entries.insert(0, entry)
        self.entries = self.entries[: self.MAX_ENTRIES]
        self.save_history()
        self._render()

    def load_history(self) -> None:
        """Load history entries from QSettings."""
        raw = self.settings.value(self.SETTINGS_KEY, "[]")
        if not isinstance(raw, str):
            raw = "[]"
        try:
            payload = json.loads(raw)
            self.entries = [
                GenerationHistoryEntry(
                    name=str(item.get("name", "")),
                    theme=str(item.get("theme", "")),
                    level_range=str(item.get("level_range", "")),
                    status=str(item.get("status", "")),
                    duration_seconds=float(item.get("duration_seconds", 0.0)),
                )
                for item in payload
                if isinstance(item, dict)
            ][: self.MAX_ENTRIES]
        except (TypeError, ValueError, json.JSONDecodeError):
            self.entries = []
        self._render()

    def save_history(self) -> None:
        """Save history entries to QSettings."""
        payload = [asdict(entry) for entry in self.entries[: self.MAX_ENTRIES]]
        self.settings.setValue(self.SETTINGS_KEY, json.dumps(payload))
        self.settings.sync()

    def clear_history(self) -> None:
        """Clear persisted and visible history."""
        self.entries.clear()
        self.save_history()
        self._render()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)

    def _render(self) -> None:
        self.list_widget.clear()
        for entry in self.entries:
            self.list_widget.addItem(
                f"{entry.name} | {entry.theme} | {entry.level_range} | "
                f"{entry.status} | {entry.duration_seconds:.2f}s"
            )
