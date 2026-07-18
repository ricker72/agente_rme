"""
Small reusable PySide6 panel helpers for WG-20U.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class LivePreviewPanel(QFrame):
    """Base panel with WG-31 styling hooks."""

    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("LivePreviewPanel")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.title = QLabel(title)
        self.title.setObjectName("PanelTitle")
        self.title.setWordWrap(True)
        self.layout.addWidget(self.title)


class TablePanel(LivePreviewPanel):
    """Panel that displays a list of dictionaries."""

    def __init__(self, title: str, columns: Iterable[str]) -> None:
        super().__init__(title)
        self.columns = list(columns)
        self.table = QTableWidget(0, len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setWordWrap(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.layout.addWidget(self.table)

    def set_rows(self, rows: List[Dict[str, Any]]) -> None:
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for col_index, key in enumerate(self.columns):
                value = row.get(key, "")
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                self.table.setItem(row_index, col_index, item)
        self.table.resizeRowsToContents()
