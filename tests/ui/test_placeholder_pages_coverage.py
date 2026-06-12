from __future__ import annotations

from typing import Any

import pytest
from PySide6.QtWidgets import QLabel, QStackedWidget

from ui.navigation import NavigationController
from ui.pages.architect_page import ArchitectPage
from ui.pages.campaign_page import CampaignPage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.otbm_page import OTBMPage
from ui.pages.settings_page import SettingsPage


PLACEHOLDER_PAGES = [
    (ArchitectPage, "architect", "Architect"),
    (CampaignPage, "campaign", "Campaign"),
    (OTBMPage, "otbm", "OTBM"),
    (SettingsPage, "settings", "Settings"),
]


@pytest.mark.parametrize(("page_cls", "page_id", "title"), PLACEHOLDER_PAGES)
def test_placeholder_page_construction_and_title(
    qapp_instance: Any, page_cls: type, page_id: str, title: str
) -> None:
    page = page_cls()
    labels = page.findChildren(QLabel)

    assert page.PAGE_ID == page_id
    assert page.objectName() == page_id
    assert any(label.text() == title for label in labels)
    assert page.layout() is not None


@pytest.mark.parametrize(("page_cls", "page_id", "title"), PLACEHOLDER_PAGES)
def test_placeholder_page_build_ui_emits_on_existing_instance(
    qapp_instance: Any, page_cls: type, page_id: str, title: str
) -> None:
    page = page_cls()
    emitted: list[str] = []
    page.page_loaded.connect(emitted.append)

    page._build_ui()

    assert emitted == [page_id]
    assert any(label.text() == title for label in page.findChildren(QLabel))


def test_placeholder_pages_load_safely_through_navigation(qapp_instance: Any) -> None:
    workspace = QStackedWidget()
    nav = NavigationController(workspace=workspace)
    for page_cls, page_id, _title in PLACEHOLDER_PAGES:
        nav.register_page(page_id, page_cls)

    for _page_cls, page_id, _title in PLACEHOLDER_PAGES:
        nav.navigate_to(page_id)
        assert nav.current_page_id == page_id

    assert workspace.count() == len(PLACEHOLDER_PAGES)


def test_dashboard_page_defaults_updates_and_navigation_signal(qapp_instance: Any) -> None:
    page = DashboardPage()
    emitted: list[str] = []
    page.navigation_requested.connect(emitted.append)

    assert page.objectName() == "dashboard"
    assert len(page.metric_cards) == 6
    assert any(label.text() == "Application Overview" for label in page.findChildren(QLabel))

    page._on_data_updated({})
    assert page.metric_cards[0]._value_label.text() == "OK"
    assert page.metric_cards[1]._value_label.text() == "0 items"
    assert page.metric_cards[5]._value_label.text() == "Never"

    page._on_data_updated(
        {
            "health": {"healthy": 3, "warning": 1, "error": 2},
            "metrics": {
                "critic_status": "Running",
                "otbm_status": "Exporting",
                "autonomous_status": "Planning",
            },
            "ga_cert": {
                "knowledge_datasets": 12,
                "last_export_timestamp": "2026-06-11 22:00",
                "recent_projects": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"],
            },
        }
    )
    assert page.metric_cards[0]._value_label.text() == "ISSUES"
    assert page.metric_cards[1]._value_label.text() == "12 items"
    assert page.metric_cards[2]._value_label.text() == "Running"
    assert page.metric_cards[3]._value_label.text() == "Exporting"
    assert page.metric_cards[4]._value_label.text() == "Planning"
    assert page.metric_cards[5]._value_label.text() == "2026-06-11 22:00"

    page._on_quick_action("world")
    assert emitted == ["world"]


def test_dashboard_page_loads_through_navigation(qapp_instance: Any) -> None:
    workspace = QStackedWidget()
    nav = NavigationController(workspace=workspace)
    nav.register_page("dashboard", DashboardPage)

    nav.navigate_to("dashboard")

    assert nav.current_page_id == "dashboard"
    assert isinstance(workspace.currentWidget(), DashboardPage)
