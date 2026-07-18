from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .content_designer import ContentDesigner
from .economy_designer import EconomyDesigner
from .progression_designer import ProgressionDesigner
from .reward_designer import RewardDesigner
from .lore_generator import LoreGenerator


@dataclass
class Expansion:
    name: str
    theme: str
    cities: List[Dict[str, object]] = field(default_factory=list)
    hunts: List[Dict[str, object]] = field(default_factory=list)
    quests: List[Dict[str, object]] = field(default_factory=list)
    bosses: List[Dict[str, object]] = field(default_factory=list)
    rewards: Dict[str, object] = field(default_factory=dict)
    progression: Dict[str, object] = field(default_factory=dict)
    economy: Dict[str, object] = field(default_factory=dict)
    lore: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "theme": self.theme,
            "cities": self.cities,
            "hunts": self.hunts,
            "quests": self.quests,
            "bosses": self.bosses,
            "rewards": self.rewards,
            "progression": self.progression,
            "economy": self.economy,
            "lore": self.lore,
        }


class ExpansionDesigner:
    def __init__(self):
        self.content_designer = ContentDesigner()
        self.progression_designer = ProgressionDesigner()
        self.reward_designer = RewardDesigner()
        self.economy_designer = EconomyDesigner()
        self.lore_generator = LoreGenerator()

    def design(self, prompt: str) -> Expansion:
        theme = self._infer_theme(prompt)
        name = self._create_name(theme)
        progression = self.progression_designer.distribute()
        content = self.content_designer.design(theme, progression)
        rewards = self.reward_designer.generate(theme, progression)
        economy = self.economy_designer.balance(theme, content)
        lore = self.lore_generator.generate(name, theme, content)

        return Expansion(
            name=name,
            theme=theme,
            cities=content.get("cities", []),
            hunts=content.get("hunts", []),
            quests=content.get("quests", []),
            bosses=content.get("bosses", []),
            rewards=rewards,
            progression=progression,
            economy=economy,
            lore=lore,
        )

    def _infer_theme(self, prompt: str) -> str:
        lower = prompt.lower()
        if "roshamuul" in lower:
            return "Roshamuul"
        if "issavi" in lower:
            return "Issavi"
        if "hybrid" in lower:
            return "Twilight"
        return "Mythic"

    def _create_name(self, theme: str) -> str:
        if theme.lower() == "roshamuul":
            return "Roshamuul Ascendancy"
        if theme.lower() == "issavi":
            return "Issavi Reborn"
        if theme.lower() == "twilight":
            return "Twilight Frontier"
        return f"{theme} Expansion"
