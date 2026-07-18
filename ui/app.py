"""
Application entry-point for Agente RME Studio.

Creates the QApplication instance, applies the dark theme,
and shows the main window.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .event_bus import EventBus
from .main_window import MainWindow
from .theme import ThemeManager


class RMEStudioApp:
    """Top-level application container.

    Usage::

        app = RMEStudioApp(sys.argv)
        app.run()

    The application can also be launched via ``python -m ui`` once the
    package is installed.
    """

    def __init__(self, argv: list[str] | None = None) -> None:
        self._argv = argv or sys.argv

        # Infrastructure
        self._event_bus = EventBus()
        self._theme = ThemeManager()

        # Qt application
        self._qt_app = QApplication(self._argv)
        self._qt_app.setApplicationName("Agente RME Studio")
        self._qt_app.setOrganizationName("OpenTibiaBR")
        self._qt_app.setApplicationVersion("2.0.0")

        # Apply global stylesheet
        self._qt_app.setStyleSheet(self._theme.global_stylesheet())

        # Main window
        self._main_window = MainWindow(
            theme=self._theme,
            event_bus=self._event_bus,
        )

    # ── properties ──────────────────────────────────────────────────────

    @property
    def event_bus(self) -> EventBus:
        """The application-wide event bus."""
        return self._event_bus

    @property
    def theme(self) -> ThemeManager:
        """The application-wide theme manager."""
        return self._theme

    @property
    def main_window(self) -> MainWindow:
        """The application's main window."""
        return self._main_window

    @property
    def qt_app(self) -> QApplication:
        """The underlying QApplication instance."""
        return self._qt_app

    # ── public API ──────────────────────────────────────────────────────

    def run(self) -> int:
        """Show the main window and enter the Qt event loop.

        Returns the exit code that should be passed to ``sys.exit()``.
        """
        self._main_window.show()
        return self._qt_app.exec()

    @staticmethod
    def run_standalone(argv: list[str] | None = None) -> int:
        """Convenience entry point::

        sys.exit(RMEStudioApp.run_standalone())
        """
        app = RMEStudioApp(argv)
        return app.run()
