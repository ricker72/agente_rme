"""
WG-31 dark professional theme for WG-20U.
"""

from __future__ import annotations

BACKGROUND = "#0F1115"
PANEL = "#161A22"
CARD = "#1D2330"
PRIMARY_GOLD = "#D4AF37"
TEXT = "#FFFFFF"
MUTED_TEXT = "#AEB6C3"
ERROR = "#E05252"
WARNING = "#E0A64B"
SUCCESS = "#57C785"


def stylesheet() -> str:
    """Return the WG-31 live preview stylesheet."""
    return f"""
    QMainWindow, QWidget {{
        background-color: {BACKGROUND};
        color: {TEXT};
        font-family: "Segoe UI", "Arial", "Noto Sans", sans-serif;
        font-size: 12px;
    }}
    QFrame#LivePreviewPanel, QGroupBox {{
        background-color: {PANEL};
        border: 1px solid {CARD};
        border-radius: 6px;
    }}
    QLabel#PanelTitle {{
        color: {PRIMARY_GOLD};
        font-weight: 600;
        padding-bottom: 4px;
    }}
    QLabel#PageTitle {{
        color: {TEXT};
        font-size: 22px;
        font-weight: 700;
    }}
    QLabel#Notification {{
        background-color: {CARD};
        color: {TEXT};
        border: 1px solid #2A3242;
        border-radius: 6px;
        padding: 8px 10px;
    }}
    QLabel#Notification[level="warning"] {{
        border-color: {WARNING};
        color: {WARNING};
    }}
    QLabel#Notification[level="error"] {{
        border-color: {ERROR};
        color: {ERROR};
    }}
    QListWidget#StudioSidebar {{
        background-color: {PANEL};
        border: 1px solid {CARD};
        border-radius: 6px;
        padding: 4px;
    }}
    QListWidget#StudioSidebar::item {{
        min-height: 34px;
        border-radius: 4px;
        padding: 6px 8px;
    }}
    QListWidget#StudioSidebar::item:selected {{
        background-color: {PRIMARY_GOLD};
        color: {BACKGROUND};
    }}
    QProgressBar {{
        background-color: {CARD};
        color: {TEXT};
        border: 1px solid #2A3242;
        border-radius: 4px;
        min-height: 18px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background-color: {PRIMARY_GOLD};
        border-radius: 4px;
    }}
    QTableWidget, QListWidget, QPlainTextEdit, QTextEdit {{
        background-color: {CARD};
        color: {TEXT};
        border: 1px solid #2A3242;
        gridline-color: #2A3242;
        selection-background-color: {PRIMARY_GOLD};
        selection-color: #0F1115;
    }}
    QPushButton, QComboBox, QSpinBox {{
        background-color: {CARD};
        color: {TEXT};
        border: 1px solid #2A3242;
        border-radius: 4px;
        padding: 4px 8px;
    }}
    QPushButton:hover {{
        border-color: {PRIMARY_GOLD};
    }}
    QSlider::groove:horizontal {{
        background: {CARD};
        height: 4px;
    }}
    QSlider::handle:horizontal {{
        background: {PRIMARY_GOLD};
        width: 12px;
        margin: -4px 0;
        border-radius: 6px;
    }}
    """
