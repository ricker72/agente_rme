"""
Console output panel for Agente RME Studio.

Displays log messages from agents, services, and the application itself.
Messages are colour-coded by severity level.
"""

from __future__ import annotations

from PySide6.QtCore import Slot
from PySide6.QtGui import QColor, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QWidget

from .event_bus import ConsoleMessageEvent, EventBus
from .theme import ThemeManager


class ConsolePanel(QPlainTextEdit):
    """Read-only console with colour-coded log output."""

    MAX_BLOCKS: int = 10_000

    def __init__(
        self,
        parent: QWidget | None = None,
        theme: ThemeManager | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme or ThemeManager()
        self._event_bus = event_bus

        self.setReadOnly(True)
        self.setObjectName("ConsolePanel")
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setMaximumBlockCount(self.MAX_BLOCKS)

        self._apply_styles()

        if self._event_bus is not None:
            self._event_bus.register(ConsoleMessageEvent, self._on_console_message)  # type: ignore[arg-type]

    # ── styling ─────────────────────────────────────────────────────────

    def _apply_styles(self) -> None:
        p = self._theme.palette
        self.setStyleSheet(
            f"""
            QPlainTextEdit#ConsolePanel {{
                background-color: {p.console_background};
                color: {p.console_foreground};
                border: none;
                font-family: 'Consolas', 'Fira Code', 'Courier New', monospace;
                font-size: 12px;
                padding: 4px;
            }}
            """
        )

    # ── colour helpers ──────────────────────────────────────────────────

    @staticmethod
    def _colour_for_level(level: str) -> QColor:
        # These will be customised per-theme in a later iteration
        mapping = {
            "info": QColor("#6A9955"),
            "warn": QColor("#CE9178"),
            "error": QColor("#F44747"),
            "debug": QColor("#569CD6"),
        }
        return mapping.get(level, QColor("#CCCCCC"))

    # ── event handler ───────────────────────────────────────────────────

    @Slot()
    def _on_console_message(self, event: ConsoleMessageEvent) -> None:
        """Append a colour-coded message to the console."""
        prefix = event.level.upper().ljust(5)

        source = f"[{event.source}] " if event.source else ""
        line = f"{prefix} {source}{event.message}"

        self.appendPlainText(line)
        # Auto-scroll to bottom
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cursor)

    # ── public helpers ──────────────────────────────────────────────────

    def log(self, message: str, level: str = "info", source: str = "") -> None:
        """Manually log a line without going through the event bus."""
        self._on_console_message(
            ConsoleMessageEvent(level=level, message=message, source=source)
        )

    def clear_console(self) -> None:
        """Remove all content from the console."""
        self.clear()
