"""
Unit tests for MetricCard widget.
"""

import pytest
from PySide6.QtWidgets import QApplication
from ui.widgets.metric_card import MetricCard


@pytest.fixture(scope="module")
def app():
    """Create a QApplication for the test session."""
    return QApplication.instance() or QApplication([])


def test_metric_card_initial_state(app):
    card = MetricCard()
    # Default labels should be empty
    assert card._title_label.text() == ""
    assert card._value_label.text() == ""
    assert card._icon_label.text() == ""


def test_metric_card_update(app):
    card = MetricCard()
    card.update_metric(title="Test Title", value="42", icon="star")
    assert card._title_label.text() == "Test Title"
    assert card._value_label.text() == "42"
    # Icon mapping for "star" should be a star emoji
    assert card._icon_label.text() == "\u2b50"
