from __future__ import annotations

from PySide6.QtWidgets import QPushButton

from ui.sidebar import Sidebar


def _sidebar_buttons(sidebar: Sidebar) -> dict[str, QPushButton]:
    return {
        button.objectName().replace("SidebarButton_", ""): button
        for button in sidebar.findChildren(QPushButton)
    }


def test_sidebar_exposes_autonomous_action(qapp_instance: object) -> None:
    sidebar = Sidebar()
    buttons = _sidebar_buttons(sidebar)

    assert "autonomous" in buttons
    assert buttons["autonomous"].toolTip() == "Autonomous"
    assert buttons["autonomous"].objectName() == "SidebarButton_autonomous"


def test_sidebar_autonomous_click_emits_navigation(qapp_instance: object) -> None:
    sidebar = Sidebar()
    emitted: list[str] = []
    sidebar.page_changed.connect(emitted.append)

    _sidebar_buttons(sidebar)["autonomous"].click()

    assert emitted == ["autonomous"]


def test_sidebar_keeps_existing_page_actions(qapp_instance: object) -> None:
    sidebar = Sidebar()
    expected = [
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

    assert [page_id for page_id, _icon, _tooltip in Sidebar.ICONS] == expected
    assert list(_sidebar_buttons(sidebar)) == expected
