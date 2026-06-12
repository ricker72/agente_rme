"""Tests for autonomous decision feed."""

from __future__ import annotations

from ui.models.autonomous_dto import AutonomousIterationDTO
from ui.widgets.autonomous_decision_feed import AutonomousDecisionFeed


def test_decision_feed_empty_state(qapp_instance: object) -> None:
    feed = AutonomousDecisionFeed()
    feed.update_from_iterations([])
    assert feed.list_widget.item(0).text() == "No decisions yet"


def test_decision_feed_renders_iterations(qapp_instance: object) -> None:
    feed = AutonomousDecisionFeed()
    feed.update_from_iterations(
        [AutonomousIterationDTO(iteration_number=1, progress=0.75, status="completed", summary="Good")]
    )
    text = feed.list_widget.item(0).text()
    assert "Decision:" in text
    assert "Impact: 0.75" in text
