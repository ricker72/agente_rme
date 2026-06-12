"""Tests for autonomous chart viewer."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QImage
from pytest import MonkeyPatch

from ui.widgets.autonomous_chart_viewer import AutonomousChartViewer


def test_chart_viewer_fallback(qapp_instance: object) -> None:
    viewer = AutonomousChartViewer()
    viewer.refresh_charts()
    assert viewer.labels["Iteration Scores"].text() == "No chart available"


def test_chart_viewer_loads_png(
    qapp_instance: object,
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    image = QImage(8, 8, QImage.Format.Format_RGB32)
    image.fill(0x224488)
    assert image.save("iteration_scores.png")
    viewer = AutonomousChartViewer()
    viewer.refresh_charts()
    pixmap = viewer.labels["Iteration Scores"].pixmap()
    assert pixmap is not None
    assert not pixmap.isNull()
