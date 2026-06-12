from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings

from ui.main_window import MainWindow


def _workspace_object_names(window: MainWindow) -> list[str]:
    names: list[str] = []
    for index in range(window.workspace.count()):
        widget = window.workspace.widget(index)
        if widget is not None:
            names.append(widget.objectName())
    return names


def test_main_window_registers_autonomous_page_lazily(qapp_instance: object) -> None:
    QSettings().clear()
    window = MainWindow()
    try:
        assert window.navigation is not None
        assert "autonomous" in window.navigation.registered_ids()
        assert "dashboard" in window.navigation.registered_ids()
        assert "autonomous" not in _workspace_object_names(window)

        initial_count = window.workspace.count()
        window._on_page_changed("autonomous")

        assert window.navigation.current_page_id == "autonomous"
        assert window.workspace.currentWidget().objectName() == "autonomous"
        assert window.workspace.count() == initial_count + 1

        window._on_page_changed("autonomous")
        assert window.workspace.count() == initial_count + 1
    finally:
        window.close()


def test_main_window_existing_pages_still_navigate(qapp_instance: object) -> None:
    QSettings().clear()
    window = MainWindow()
    page_ids = [
        "dashboard",
        "world",
        "architect",
        "critic",
        "knowledge",
        "campaign",
        "otbm",
        "autonomous",
        "settings",
    ]
    try:
        assert window.navigation is not None
        assert set(window.navigation.registered_ids()) == set(page_ids)
        for page_id in page_ids:
            window._on_page_changed(page_id)
            assert window.navigation.current_page_id == page_id
            assert window.workspace.currentWidget().layout() is not None
    finally:
        window.close()


def test_shell_navigation_files_do_not_import_core() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [Path("ui/main_window.py"), Path("ui/sidebar.py")]
    )
    assert "import core" not in text
    assert "from core" not in text
    assert "import agents" not in text
    assert "from agents" not in text
