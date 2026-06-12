"""Tests for critic score widgets."""

from __future__ import annotations

from ui.models.critic_dto import CriticDTO
from ui.widgets.critic_report_summary import CriticReportSummary
from ui.widgets.critic_score_card import CriticScoreCard
from ui.widgets.critic_score_grid import CriticScoreGrid


def test_score_card_renders_status(qapp_instance: object) -> None:
    card = CriticScoreCard("Overall")
    card.update_score(92.0)
    assert card.score_label.text() == "92.0"
    assert card.status_label.text() == "Excellent"
    card.update_score(None)
    assert card.score_label.text() == "-"


def test_score_grid_updates_overall_score(qapp_instance: object) -> None:
    grid = CriticScoreGrid()
    grid.update_scores(CriticDTO(score=74.5))
    assert grid.cards["Overall Score"].score_label.text() == "74.5"
    assert grid.cards["Navigation Score"].score_label.text() == "-"


def test_report_summary_renders_counts(qapp_instance: object) -> None:
    summary = CriticReportSummary()
    report = CriticDTO(score=80.0, suggestions=["Add route"], summary="Complete")
    summary.update_report(report)
    assert summary.overall_score_value.text() == "80.0"
    assert summary.recommendations_value.text() == "1"
    assert summary.status_value.text() == "Complete"
