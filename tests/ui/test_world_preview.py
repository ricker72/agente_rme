"""Tests for world preview widget."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QImage

from ui.widgets.world_preview_widget import WorldPreviewWidget


def test_preview_fallback_for_missing_image(qapp_instance: object) -> None:
    widget = WorldPreviewWidget()
    assert not widget.load_preview("missing_preview.png")
    assert widget.preview_label.text() == "No preview available"


def test_preview_loads_existing_image(qapp_instance: object, tmp_path: Path) -> None:
    path = tmp_path / "generated_preview.png"
    image = QImage(10, 10, QImage.Format.Format_RGB32)
    image.fill(0x336699)
    assert image.save(str(path))

    widget = WorldPreviewWidget()
    assert widget.load_preview(str(path))
    assert widget.preview_label.pixmap() is not None
    assert not widget.preview_label.pixmap().isNull()
