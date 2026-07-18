"""
Floor selector for WG-20U floors 0-15.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QSlider, QVBoxLayout, QWidget


class FloorSelector(QWidget):
    """Vertical floor selector constrained to floors 0-15."""

    floorChanged = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.label = QLabel("Floor 7")
        self.slider = QSlider()
        self.slider.setMinimum(0)
        self.slider.setMaximum(15)
        self.slider.setValue(7)
        self.slider.valueChanged.connect(self._on_changed)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.slider)

    def set_floor(self, floor: int) -> None:
        self.slider.setValue(max(0, min(15, floor)))

    def _on_changed(self, floor: int) -> None:
        self.label.setText(f"Floor {floor}")
        self.floorChanged.emit(floor)
