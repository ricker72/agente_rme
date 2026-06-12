from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QLabel

from ui.widgets.health_widget import HealthWidget
from ui.widgets.recent_activity_widget import RecentActivityWidget
from ui.widgets.release_info_widget import ReleaseInfoWidget
from ui.widgets.status_card import StatusCard
from ui.widgets.system_status_widget import SystemStatusWidget


def test_status_card_defaults_and_variants(qapp_instance: Any) -> None:
    card = StatusCard()
    assert card.objectName() == "status_card"
    assert card.height() == 100

    card.update_status("Build", "42", "OK", "healthy")
    assert card._title_label.text() == "Build"
    assert card._value_label.text() == "42"
    assert card._status_label.text() == "OK"
    assert "#a6e3a1" in card._status_label.styleSheet()

    card.set_status("WARN", "warning")
    assert "#f9e2af" in card._status_label.styleSheet()
    card.set_status("ERR", "error")
    assert "#f38ba8" in card._status_label.styleSheet()
    card.set_status("INFO", "unknown")
    assert "#89b4fa" in card._status_label.styleSheet()


def test_release_info_widget_refresh_defaults_and_values(qapp_instance: Any) -> None:
    widget = ReleaseInfoWidget()
    assert widget._name_label.text() == "Release: -"
    assert widget._version_label.text() == "Version: -"

    widget.refresh({"name": "UI Freeze", "version": "10.2-R"})
    assert widget._name_label.text() == "Release: UI Freeze"
    assert widget._version_label.text() == "Version: 10.2-R"

    widget.refresh({})
    assert widget._name_label.text() == "Release: -"
    assert widget._version_label.text() == "Version: -"


def test_system_status_widget_health_and_status_variants(qapp_instance: Any) -> None:
    widget = SystemStatusWidget()
    assert widget.objectName() == "system_status_widget"
    assert widget.height() == 120
    assert widget._title_label.text() == "System Status"

    widget.update_health(5, 2, 1)
    assert widget._healthy_label.text() == "HEALTHY: 5"
    assert widget._warning_label.text() == "WARNING: 2"
    assert widget._error_label.text() == "ERROR: 1"

    widget.update_status("Online", "healthy")
    assert "#a6e3a1" in widget.styleSheet()
    widget.update_status("Careful", "warning")
    assert "#f9e2af" in widget.styleSheet()
    widget.update_status("Down", "error")
    assert "#f38ba8" in widget.styleSheet()
    widget.update_status("Idle", "unknown")
    assert "#89b4fa" in widget.styleSheet()


def test_health_widget_default_and_update(qapp_instance: Any) -> None:
    widget = HealthWidget()
    assert widget.objectName() == "health_widget"
    assert widget.height() == 120
    assert widget._title_label.text() == "Health Status"

    widget.update_health(7, 0, 3)
    assert widget._healthy_label.text() == "HEALTHY: 7"
    assert widget._warning_label.text() == "WARNING: 0"
    assert widget._error_label.text() == "ERROR: 3"


def test_recent_activity_widget_empty_missing_and_full_refresh(qapp_instance: Any) -> None:
    widget = RecentActivityWidget()
    labels = {label.objectName(): label.text() for label in widget.findChildren(QLabel)}
    assert labels["activity_export"] == "Export: -"
    assert labels["activity_critic"] == "Critic: -"
    assert labels["activity_knowledge"] == "Knowledge: -"
    assert labels["activity_campaign"] == "Campaign: -"

    widget.refresh({"export": "now", "campaign": "later"})
    labels = {label.objectName(): label.text() for label in widget.findChildren(QLabel)}
    assert labels["activity_export"] == "Export: now"
    assert labels["activity_critic"] == "Critic: -"
    assert labels["activity_knowledge"] == "Knowledge: -"
    assert labels["activity_campaign"] == "Campaign: later"
