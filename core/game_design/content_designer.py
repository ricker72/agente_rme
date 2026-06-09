from __future__ import annotations

from typing import Dict, List

from .boss_designer import BossDesigner
from .hunt_designer import HuntDesigner
from .quest_designer import QuestDesigner


class ContentDesigner:
    def __init__(self):
        self.hunt_designer = HuntDesigner()
        self.quest_designer = QuestDesigner()
        self.boss_designer = BossDesigner()

    def design(self, theme: str, progression: Dict[str, object]) -> Dict[str, object]:
        cities = self._design_cities(theme)
        bosses = self._design_bosses(theme, progression)
        hunts = self._design_hunts(theme, progression)
        quests = self._design_quests(theme, bosses)

        return {
            "cities": cities,
            "hunts": hunts,
            "bosses": bosses,
            "quests": quests,
        }

    def _design_cities(self, theme: str) -> List[Dict[str, object]]:
        return [
            {
                "name": f"{theme} City",
                "theme": theme,
                "population": 1200,
                "description": f"A sprawling capital that anchors the {theme} expansion.",
                "districts": ["Market", "Temple", "Harbor"],
            }
        ]

    def _design_hunts(self, theme: str, progression: Dict[str, object]) -> List[Dict[str, object]]:
        hunts = []
        for i, tier in enumerate(progression.get("tiers", []), start=1):
            if i > 3:
                break
            hunts.append(self.hunt_designer.design(recommended_level=tier.get("recommended_level", "50-100"), theme=theme, index=i))
        return hunts

    def _design_bosses(self, theme: str, progression: Dict[str, object]) -> List[Dict[str, object]]:
        bosses = []
        for index, tier in enumerate(progression.get("tiers", []), start=1):
            if index > 5:
                break
            bosses.append(self.boss_designer.design(theme=theme, difficulty=tier.get("difficulty", "hard"), index=index))
        return bosses

    def _design_quests(self, theme: str, bosses: List[Dict[str, object]]) -> List[Dict[str, object]]:
        quest_chain = []
        quest_chain.append(self.quest_designer.design("story", theme, f"Begin the {theme} saga."))
        quest_chain.append(self.quest_designer.design("exploration", theme, "Survey the outer wilds."))
        if bosses:
            quest_chain.append(self.quest_designer.design("boss", theme, f"Confront {bosses[0].get('name')}"))
        quest_chain.append(self.quest_designer.design("collection", theme, "Gather relics for the city."))
        quest_chain.append(self.quest_designer.design("puzzle", theme, "Unlock the ancient gate."))
        return quest_chain
