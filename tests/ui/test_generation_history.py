"""Tests for generation history persistence."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings

from ui.widgets.generation_history_widget import (
    GenerationHistoryEntry,
    GenerationHistoryWidget,
)


def _settings(path: Path) -> QSettings:
    return QSettings(str(path), QSettings.Format.IniFormat)


def test_history_persists_entries(qapp_instance: object, tmp_path: Path) -> None:
    settings_path = tmp_path / "history.ini"
    widget = GenerationHistoryWidget(_settings(settings_path))
    widget.clear_history()
    widget.add_entry(
        GenerationHistoryEntry(
            name="World",
            theme="Issavi",
            level_range="300-500",
            status="Generated",
            duration_seconds=1.25,
        )
    )

    reloaded = GenerationHistoryWidget(_settings(settings_path))
    assert len(reloaded.entries) == 1
    assert reloaded.entries[0].name == "World"
    assert reloaded.list_widget.count() == 1


def test_history_limits_to_20_entries(qapp_instance: object, tmp_path: Path) -> None:
    widget = GenerationHistoryWidget(_settings(tmp_path / "history.ini"))
    widget.clear_history()
    for index in range(25):
        widget.add_entry(
            GenerationHistoryEntry(
                name=f"World {index}",
                theme="Falcon",
                level_range="1-2",
                status="Generated",
                duration_seconds=0.1,
            )
        )
    assert len(widget.entries) == 20
    assert widget.entries[0].name == "World 24"
