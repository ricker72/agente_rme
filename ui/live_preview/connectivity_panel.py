"""
WG-20U connectivity panel.
"""

from __future__ import annotations

from typing import Any, Dict

from PySide6.QtWidgets import QPlainTextEdit

from .base_panel import LivePreviewPanel


class ConnectivityPanel(LivePreviewPanel):
    """Consumes WG-20TE connectivity datasets."""

    def __init__(self) -> None:
        super().__init__("Connectivity")
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.layout.addWidget(self.text)

    def set_data(self, data: Dict[str, Any]) -> None:
        lines = [
            f"Floor Graph: {len(data.get('floor_nodes', []))} floors",
            f"Stair Links: {len(data.get('stairs', data.get('floor_edges', [])))}",
            f"Ramp Links: {len(data.get('ramps', []))}",
            f"Building Accessibility: {data.get('accessibility_status', 'UNKNOWN')}",
            f"Hunt Accessibility: {data.get('hunt_accessibility', 'UNKNOWN')}",
            f"Connectivity Warnings: {len(data.get('orphan_connectors', []))}",
        ]
        self.text.setPlainText("\n".join(lines))
