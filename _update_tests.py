"""Helper script to update test files with QApplication fixture."""

# Update test_dashboard_page.py
with open("tests/ui/test_dashboard_page.py", "w", encoding="utf-8") as f:
    f.write('''"""
Tests for Dashboard Page widgets.
"""
import pytest


def test_dashboard_page_id():
    from ui.pages.dashboard_page import DashboardPage
    assert DashboardPage.PAGE_ID == "dashboard"


def test_metric_card_title(qapp_instance):
    from ui.widgets.metric_card import MetricCard
    card = MetricCard()
    card.set_title("Test Title")
    assert card._title_label.text() == "Test Title"


def test_metric_card_value(qapp_instance):
    from ui.widgets.metric_card import MetricCard
    card = MetricCard()
    card.set_value("42")
    assert card._value_label.text() == "42"


def test_metric_card_icon(qapp_instance):
    from ui.widgets.metric_card import MetricCard
    card = MetricCard()
    card.set_icon("star")
    assert card._icon_label.text() == "\\u2b50"


def test_health_widget(qapp_instance):
    from ui.widgets.health_widget import HealthWidget
    widget = HealthWidget()
    widget.update_health(5, 2, 1)
    assert "5" in widget._healthy_label.text()
    assert "2" in widget._warning_label.text()
    assert "1" in widget._error_label.text()
''')

# Update test_recent_artifacts.py
with open("tests/ui/test_recent_artifacts.py", "w", encoding="utf-8") as f:
    f.write('''"""
Tests for Recent Artifacts Widget.
"""
from dataclasses import dataclass


@dataclass
class FakeArtifact:
    name: str
    modified: str
    size: str


def test_recent_artifacts_initial_state(qapp_instance):
    from ui.widgets.recent_artifacts_widget import RecentArtifactsWidget
    widget = RecentArtifactsWidget()
    assert widget._table.rowCount() == 0


def test_recent_artifacts_update(qapp_instance):
    from ui.widgets.recent_artifacts_widget import RecentArtifactsWidget
    widget = RecentArtifactsWidget()
    artifacts = [
        FakeArtifact("file1.otbm", "2026-01-01", "1.5 MB"),
        FakeArtifact("file2.png", "2026-01-02", "500 KB"),
    ]
    widget.update_artifacts(artifacts)
    assert widget._table.rowCount() == 2
    assert widget._table.item(0, 0).text() == "file1.otbm"
    assert widget._table.item(1, 0).text() == "file2.png"
''')

print("Test files updated successfully.")
