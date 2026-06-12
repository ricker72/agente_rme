"""
Unit tests for SystemHealthWidget.
"""

import pytest
from PySide6.QtWidgets import QApplication
from ui.widgets.system_health_widget import SystemHealthWidget


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_system_health_initial_state(app):
    widget = SystemHealthWidget()
    # Default labels should show zero counts
    assert widget._healthy_label.text() == "HEALTHY: 0"
    assert widget._warning_label.text() == "WARNING: 0"
    assert widget._error_label.text() == "ERROR: 0"


def test_system_health_update(app):
    widget = SystemHealthWidget()
    widget.update_health(healthy=5, warning=2, error=1)
    assert widget._healthy_label.text() == "HEALTHY: 5"
    assert widget._warning_label.text() == "WARNING: 2"
    assert widget._error_label.text() == "ERROR: 1"
