"""Tests for critic heatmap viewer."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QImage

from ui.models.critic_dto import HeatmapDTO
from ui.widgets.critic_heatmap_viewer import CriticHeatmapViewer


def test_heatmap_viewer_fallback(qapp_instance: object) -> None:
    viewer = CriticHeatmapViewer()
    viewer.update_heatmaps([])
    assert viewer.labels["Density Heatmap"].text() == "No heatmap available"


def test_heatmap_viewer_loads_png(qapp_instance: object, tmp_path: Path) -> None:
    path = tmp_path / "density_heatmap.png"
    image = QImage(8, 8, QImage.Format.Format_RGB32)
    image.fill(0x884422)
    assert image.save(str(path))
    viewer = CriticHeatmapViewer()
    viewer.update_heatmaps([HeatmapDTO(heatmap_id=str(path), title="Density Heatmap")])
    pixmap = viewer.labels["Density Heatmap"].pixmap()
    assert pixmap is not None
    assert not pixmap.isNull()
