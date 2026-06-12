"""
Sidebar navigation panel for Agente RME Studio.

Contains icon-based action buttons for switching between workspace pages.
Now fully integrated with the NavigationController.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .theme import ThemeManager


class Sidebar(QWidget):
    """Vertical icon toolbar on the left of the main window."""

    page_changed = Signal(str)

    # All 9 workspace pages with display label, icon, and page ID
    ICONS: list[tuple[str, str, str]] = [
        ("dashboard", "\U0001f4ca", "Dashboard"),  # dashboard
        ("world", "\U0001f5fa", "World"),  # world / map
        ("architect", "\u269b", "Architect"),  # architect
        ("critic", "\u2699", "Critic"),  # critic / analysis
        ("knowledge", "\U0001f4d6", "Knowledge"),  # knowledge base
        ("campaign", "\U0001f3f7", "Campaign"),  # campaigns
        ("otbm", "\U0001f4e6", "OTBM"),  # OTBM export
        ("autonomous", "\u25c7", "Autonomous"),  # autonomous designer
        ("settings", "\u2699\ufe0f", "Settings"),  # settings
    ]

    def __init__(
        self,
        parent: QWidget | None = None,
        theme: ThemeManager | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme or ThemeManager()

        self.setObjectName("Sidebar")
        self.setFixedWidth(48)

        self._build_ui()
        self._apply_styles()

    # ── layout ──────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        for page_id, icon_text, tooltip in self.ICONS:
            btn = QPushButton(icon_text, self)
            btn.setObjectName(f"SidebarButton_{page_id}")
            btn.setFixedSize(48, 48)
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(
                lambda _checked=False, pid=page_id: self.page_changed.emit(pid)
            )
            layout.addWidget(btn)

        layout.addStretch()

    # ── styling ─────────────────────────────────────────────────────────

    def _apply_styles(self) -> None:
        p = self._theme.palette
        self.setStyleSheet(
            f"""
            QWidget#Sidebar {{
                background-color: {p.sidebar_background};
                border-right: 1px solid {p.border};
            }}
            QPushButton {{
                background: transparent;
                color: {p.sidebar_icon};
                border: none;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {p.sidebar_active};
            }}
            """
        )
