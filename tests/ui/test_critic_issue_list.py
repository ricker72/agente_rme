"""Tests for critic issue list."""

from __future__ import annotations

from ui.models.critic_dto import CriticIssueDTO
from ui.widgets.critic_issue_list import CriticIssueList


def test_issue_list_renders_empty_state(qapp_instance: object) -> None:
    widget = CriticIssueList()
    widget.update_issues([])
    assert widget.list_widget.item(0).text() == "No issues"


def test_issue_list_renders_issue_details(qapp_instance: object) -> None:
    widget = CriticIssueList()
    widget.update_issues(
        [
            CriticIssueDTO(
                code="NAV",
                severity="critical",
                message="Missing route",
            )
        ]
    )
    text = widget.list_widget.item(0).text()
    assert "CRITICAL" in text
    assert "NAV" in text
    assert "Missing route" in text
    assert "Coordinates" in text
