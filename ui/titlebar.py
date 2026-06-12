"""
Custom title-bar widget for Agente RME Studio.

Replaces the native OS title bar with a dark-themed, flat bar that
includes the application icon, title, and window-control buttons
(minimise, maximise, close).
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from .theme import ThemeManager


class TitleBarButton(QPushButton):
    """A single flat button used in the custom title bar."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setFixedSize(46, 32)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(Qt.CursorShape.ArrowCursor)


class TitleBar(QWidget):
    """Custom title bar with window controls."""

    # Signals emitted when the user clicks a control button
    minimise_signal = Signal()
    maximise_signal = Signal()
    close_signal = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        theme: ThemeManager | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme or ThemeManager()
        self._dragging = False
        self._drag_position: QPoint | None = None

        self.setObjectName("TitleBar")
        self.setFixedHeight(32)

        self._build_ui()
        self._apply_styles()

    # ── layout ──────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(0)

        # Icon + title
        self._icon_label = QLabel(self)
        self._icon_label.setFixedSize(20, 20)
        # self._icon_label.setPixmap(...)  # future: app icon

        self._title_label = QLabel("Agente RME Studio", self)
        self._title_label.setStyleSheet("font-size: 12px; font-weight: 600;")

        layout.addWidget(self._icon_label)
        layout.addSpacing(8)
        layout.addWidget(self._title_label)
        layout.addStretch()

        # Window control buttons
        self._btn_minimise = TitleBarButton("\u2014", self)
        self._btn_maximise = TitleBarButton("\u25a1", self)
        self._btn_close = TitleBarButton("\u2715", self)

        self._btn_minimise.clicked.connect(self.minimise_signal.emit)
        self._btn_maximise.clicked.connect(self.maximise_signal.emit)
        self._btn_close.clicked.connect(self.close_signal.emit)

        layout.addWidget(self._btn_minimise)
        layout.addWidget(self._btn_maximise)
        layout.addWidget(self._btn_close)

    # ── styling ─────────────────────────────────────────────────────────

    def _apply_styles(self) -> None:
        p = self._theme.palette
        self.setStyleSheet(
            f"""
            QWidget#TitleBar {{
                background-color: {p.title_background};
                color: {p.title_foreground};
            }}
            QPushButton {{
                background: transparent;
                color: {p.title_foreground};
                border: none;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {p.title_button_hover};
            }}
            QPushButton:last-child:hover {{
                background-color: {p.title_close_hover};
            }}
            """
        )

    # ── window dragging ─────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_position = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            return
        if self._dragging and self._drag_position is not None:
            delta = event.globalPosition().toPoint() - self._drag_position
            window = self.window()
            if window:
                window.move(window.x() + delta.x(), window.y() + delta.y())
            self._drag_position = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            return
        self._dragging = False
        self._drag_position = None
        super().mouseReleaseEvent(event)

    # ── public helpers ──────────────────────────────────────────────────

    def set_title(self, text: str) -> None:
        """Update the visible window title."""
        self._title_label.setText(text)
