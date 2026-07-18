"""Score grid for Visual Critic Studio."""

from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QGroupBox, QWidget

from ui.models.critic_dto import CriticDTO
from ui.widgets.critic_score_card import CriticScoreCard


class CriticScoreGrid(QGroupBox):
    """Render all critic category score cards."""

    SCORE_TITLES = [
        "Overall Score",
        "Visual Score",
        "Navigation Score",
        "Density Score",
        "Spawn Score",
        "Hunt Score",
        "Boss Score",
        "City Score",
        "Decor Score",
        "Pathfinding Score",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Scores", parent)
        self.cards: dict[str, CriticScoreCard] = {}
        self._build_ui()

    def update_scores(self, report: CriticDTO) -> None:
        """Update cards from a critic report."""
        for title, card in self.cards.items():
            if title == "Overall Score":
                card.update_score(report.score)
            else:
                card.update_score(None)

    def _build_ui(self) -> None:
        layout = QGridLayout(self)
        layout.setSpacing(10)
        for index, title in enumerate(self.SCORE_TITLES):
            card = CriticScoreCard(title, self)
            self.cards[title] = card
            layout.addWidget(card, index // 2, index % 2)
