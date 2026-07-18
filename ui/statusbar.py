"""
Status bar widget for Agente RME Studio.

Displays contextual messages, service states, and quick-action indicators.
"""

from __future__ import annotations

from PySide6.QtCore import QTimer, Slot
from PySide6.QtWidgets import QLabel, QStatusBar, QWidget

from .event_bus import EventBus, StatusMessageEvent, ServiceStateChangedEvent
from .theme import ThemeManager


class StatusBar(QStatusBar):
    """Custom status bar with message support and state indicators."""

    def __init__(
        self,
        parent: QWidget | None = None,
        theme: ThemeManager | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme or ThemeManager()
        self._event_bus = event_bus
        self._clear_timer = QTimer(self)
        self._clear_timer.setSingleShot(True)
        self._clear_timer.timeout.connect(self._clear_timed_message)

        self.setObjectName("StatusBar")

        # Permanent widgets (right side)
        self._service_label = QLabel(self)
        self._service_label.setText("Ready")
        self.addPermanentWidget(self._service_label)

        self._apply_styles()

        if self._event_bus is not None:
            self._event_bus.register(StatusMessageEvent, self._on_status_message)  # type: ignore[arg-type]
            self._event_bus.register(ServiceStateChangedEvent, self._on_service_state)  # type: ignore[arg-type]

    # ── styling ─────────────────────────────────────────────────────────

    def _apply_styles(self) -> None:
        p = self._theme.palette
        self.setStyleSheet(
            f"""
            QStatusBar {{
                background-color: {p.status_background};
                color: {p.status_foreground};
                font-size: 12px;
                padding: 2px 8px;
                border-top: 1px solid {p.border};
            }}
            QStatusBar::item {{
                border: none;
            }}
            QLabel {{
                color: {p.status_foreground};
                padding: 0 4px;
            }}
            """
        )

    # ── event handlers ──────────────────────────────────────────────────

    @Slot()
    def _on_status_message(self, event: StatusMessageEvent) -> None:
        """Display a status message, optionally auto-clearing after a timeout."""
        self.showMessage(event.message)
        if event.timeout_ms > 0:
            self._clear_timer.start(event.timeout_ms)

    @Slot()
    def _on_service_state(self, event: ServiceStateChangedEvent) -> None:
        """Update the service state indicator."""
        self._service_label.setText(f"{event.service_name}: {event.state}")

    def _clear_timed_message(self) -> None:
        """Clear the temporary status message."""
        self.clearMessage()

    # ── public helpers ──────────────────────────────────────────────────

    def set_service_state(self, name: str, state: str) -> None:
        """Manually set the service state indicator."""
        self._service_label.setText(f"{name}: {state}")

    def set_status(self, message: str, timeout_ms: int = 0) -> None:
        """Manually set a persistent or timed status message."""
        self._on_status_message(
            StatusMessageEvent(message=message, timeout_ms=timeout_ms)
        )
