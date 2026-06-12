"""
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
