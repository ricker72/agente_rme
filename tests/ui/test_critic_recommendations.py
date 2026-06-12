"""Tests for critic recommendations."""

from __future__ import annotations

from ui.widgets.critic_recommendation_list import CriticRecommendationList


def test_recommendation_list_empty_state(qapp_instance: object) -> None:
    widget = CriticRecommendationList()
    widget.update_recommendations([])
    assert widget.list_widget.item(0).text() == "No recommendations"


def test_recommendation_list_renders_rows(qapp_instance: object) -> None:
    widget = CriticRecommendationList()
    widget.update_recommendations(["Add secondary route to boss arena"])
    text = widget.list_widget.item(0).text()
    assert "HIGH" in text
    assert "Action: Add secondary route to boss arena" in text
    assert "Target Region" in text
