"""Helper script to create test files."""

import os

os.makedirs("tests/ui", exist_ok=True)

# test_dashboard_provider.py
with open("tests/ui/test_dashboard_provider.py", "w", encoding="utf-8") as f:
    f.write("""\"\"\"
Tests for Dashboard Data Provider.
\"\"\"
import json
import os
import tempfile
from pathlib import Path


def test_dashboard_data_provider_no_data():
    from ui.dashboard_data_provider import DashboardDataProvider
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = DashboardDataProvider(base_dir=tmpdir)
        metrics = provider.get_metrics()
        assert len(metrics) == 6


def test_dashboard_data_provider_health():
    from ui.dashboard_data_provider import DashboardDataProvider
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "output")
        os.makedirs(output_dir)
        health_data = {"status": "healthy"}
        with open(os.path.join(output_dir, "health_report.json"), "w") as f:
            json.dump(health_data, f)
        provider = DashboardDataProvider(base_dir=tmpdir)
        health = provider.get_health()
        assert health.healthy == 1


def test_dashboard_data_provider_artifacts():
    from ui.dashboard_data_provider import DashboardDataProvider
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "output")
        os.makedirs(output_dir)
        Path(os.path.join(output_dir, "generated.otbm")).touch()
        provider = DashboardDataProvider(base_dir=tmpdir)
        artifacts = provider.get_artifacts()
        assert len(artifacts) == 1


def test_dashboard_data_provider_activity():
    from ui.dashboard_data_provider import DashboardDataProvider
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "output")
        os.makedirs(output_dir)
        Path(os.path.join(output_dir, "generated.otbm")).touch()
        provider = DashboardDataProvider(base_dir=tmpdir)
        activity = provider.get_activity()
        assert len(activity) == 4


def test_dashboard_data_provider_release():
    from ui.dashboard_data_provider import DashboardDataProvider
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = DashboardDataProvider(base_dir=tmpdir)
        release = provider.get_release_info()
        assert release.name == "RME Agente AI"
        assert release.version == "v1.0.0 GA"


def test_dashboard_data_provider_system_status():
    from ui.dashboard_data_provider import DashboardDataProvider
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = DashboardDataProvider(base_dir=tmpdir)
        status = provider.get_system_status()
        assert status.ui_status == "ONLINE"


def test_dashboard_data_provider_all_data():
    from ui.dashboard_data_provider import DashboardDataProvider
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = DashboardDataProvider(base_dir=tmpdir)
        data = provider.get_all_data()
        assert len(data.metrics) == 6
""")

# test_dashboard_page.py
with open("tests/ui/test_dashboard_page.py", "w", encoding="utf-8") as f:
    f.write("""\"\"\"
Tests for Dashboard Page widgets.
\"\"\"
import pytest


def test_dashboard_page_id():
    from ui.pages.dashboard_page import DashboardPage
    assert DashboardPage.PAGE_ID == "dashboard"


def test_metric_card_title():
    from ui.widgets.metric_card import MetricCard
    card = MetricCard()
    card.set_title("Test Title")
    assert card._title_label.text() == "Test Title"


def test_metric_card_value():
    from ui.widgets.metric_card import MetricCard
    card = MetricCard()
    card.set_value("42")
    assert card._value_label.text() == "42"


def test_metric_card_icon():
    from ui.widgets.metric_card import MetricCard
    card = MetricCard()
    card.set_icon("star")
    assert card._icon_label.text() == "\\u2b50"


def test_health_widget():
    from ui.widgets.health_widget import HealthWidget
    widget = HealthWidget()
    widget.update_health(5, 2, 1)
    assert "5" in widget._healthy_label.text()
    assert "2" in widget._warning_label.text()
    assert "1" in widget._error_label.text()
""")

# test_recent_artifacts.py
with open("tests/ui/test_recent_artifacts.py", "w", encoding="utf-8") as f:
    f.write("""\"\"\"
Tests for Recent Artifacts Widget.
\"\"\"
from dataclasses import dataclass


@dataclass
class FakeArtifact:
    name: str
    modified: str
    size: str


def test_recent_artifacts_initial_state():
    from ui.widgets.recent_artifacts_widget import RecentArtifactsWidget
    widget = RecentArtifactsWidget()
    assert widget._table.rowCount() == 0


def test_recent_artifacts_update():
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
""")

print("Test files created successfully.")
