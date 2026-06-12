"""
Dark-theme manager for Agente RME Studio.

Inspiration: JetBrains Darcula, Cursor, Visual Studio Dark.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemePalette:
    """Immutable colour palette used throughout the application."""

    # ── Base ────────────────────────────────────────────────────────────
    background: str = "#1E1E1E"  # main backdrop
    foreground: str = "#CCCCCC"  # default text
    alt_background: str = "#252526"  # sidebar / panels
    border: str = "#3C3C3C"

    # ── Title bar ───────────────────────────────────────────────────────
    title_background: str = "#2D2D2D"
    title_foreground: str = "#CCCCCC"
    title_button_hover: str = "#505050"
    title_close_hover: str = "#E81123"

    # ── Sidebar ─────────────────────────────────────────────────────────
    sidebar_background: str = "#252526"
    sidebar_foreground: str = "#969696"
    sidebar_active: str = "#37373D"
    sidebar_icon: str = "#CCCCCC"

    # ── Workspace ───────────────────────────────────────────────────────
    workspace_background: str = "#1E1E1E"
    workspace_foreground: str = "#CCCCCC"
    workspace_accent: str = "#007ACC"

    # ── Console ─────────────────────────────────────────────────────────
    console_background: str = "#1E1E1E"
    console_foreground: str = "#D4D4D4"
    console_info: str = "#6A9955"
    console_warn: str = "#CE9178"
    console_error: str = "#F44747"
    console_debug: str = "#569CD6"

    # ── Status bar ──────────────────────────────────────────────────────
    status_background: str = "#007ACC"
    status_foreground: str = "#FFFFFF"

    # ── Buttons ─────────────────────────────────────────────────────────
    button_background: str = "#0E639C"
    button_foreground: str = "#FFFFFF"
    button_hover: str = "#1177BB"

    # ── Scrollbar ───────────────────────────────────────────────────────
    scrollbar_background: str = "#3C3C3C"
    scrollbar_handle: str = "#686868"

    # ── Input ───────────────────────────────────────────────────────────
    input_background: str = "#3C3C3C"
    input_foreground: str = "#CCCCCC"
    input_border: str = "#5A5A5A"
    input_focus_border: str = "#007ACC"


class ThemeManager:
    """Provides the current theme palette and CSS-like stylesheet helpers.

    This is deliberately kept simple; a future version may support theme
    switching (light / dark / high-contrast).
    """

    def __init__(self, palette: ThemePalette | None = None) -> None:
        self._palette = palette or ThemePalette()

    # ── properties ──────────────────────────────────────────────────────

    @property
    def palette(self) -> ThemePalette:
        """Return the currently active palette."""
        return self._palette

    # ── stylesheet generators ───────────────────────────────────────────

    def main_window_style(self) -> str:
        """Return a QSS fragment for the main window background."""
        return f"QMainWindow {{ background-color: {self._palette.background}; }}"

    def title_bar_style(self) -> str:
        p = self._palette
        return (
            f"QWidget#TitleBar {{"
            f"  background-color: {p.title_background};"
            f"  color: {p.title_foreground};"
            f"}}"
        )

    def sidebar_style(self) -> str:
        p = self._palette
        return f"QWidget#Sidebar {{  background-color: {p.sidebar_background};}}"

    def console_style(self) -> str:
        p = self._palette
        return (
            f"QPlainTextEdit {{"
            f"  background-color: {p.console_background};"
            f"  color: {p.console_foreground};"
            f"  border: 1px solid {p.border};"
            f"}}"
        )

    def status_bar_style(self) -> str:
        p = self._palette
        return (
            f"QStatusBar {{"
            f"  background-color: {p.status_background};"
            f"  color: {p.status_foreground};"
            f"}}"
        )

    def global_stylesheet(self) -> str:
        """Return a combined global stylesheet for the entire application."""
        p = self._palette
        return f"""
        QMainWindow {{ background-color: {p.background}; }}
        QWidget {{ color: {p.foreground}; font-family: 'Segoe UI', 'Roboto', sans-serif; font-size: 13px; }}
        QPushButton {{
            background-color: {p.button_background};
            color: {p.button_foreground};
            border: none;
            padding: 4px 12px;
            border-radius: 3px;
        }}
        QPushButton:hover {{ background-color: {p.button_hover}; }}
        QLineEdit {{
            background-color: {p.input_background};
            color: {p.input_foreground};
            border: 1px solid {p.input_border};
            padding: 3px 6px;
        }}
        QLineEdit:focus {{ border-color: {p.input_focus_border}; }}
        QScrollBar:vertical {{
            background: {p.scrollbar_background};
            width: 10px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {p.scrollbar_handle};
            min-height: 20px;
            border-radius: 5px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """
