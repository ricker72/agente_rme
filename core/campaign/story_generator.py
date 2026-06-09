from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StoryArc:
    """A story arc in the campaign."""
    title: str = ""
    chapter: int = 1
    description: str = ""
    objectives: List[str] = field(default_factory=list)
    boss_name: str = ""
    reward_gold: int = 0
    reward_items: List[str] = field(default_factory=list)
    required_level: int = 1
    is_main_story: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title, "chapter": self.chapter,
            "description": self.description, "objectives": self.objectives,
            "boss_name": self.boss_name, "reward_gold": self.reward_gold,
            "reward_items": self.reward_items,
            "required_level": self.required_level,
            "is_main_story": self.is_main_story,
        }


STORY_ARCS: Dict[str, List[Dict[str, Any]]] = {
    "Issavi": [
        {"title": "Echoes of the Invasion", "chapter": 1,
         "description": "Investigate the demonic rift appearing in Issavi's sewers.",
         "objectives": ["Explore the sewers", "Defeat the Rift Guardian",
                        "Collect 5 Rift Shards"],
         "boss_name": "Rift Guardian", "reward_gold": 50000,
         "reward_items": ["Rift Sword", "Demonic Essence"],
         "required_level": 300},
        {"title": "The Shadow Council Revealed", "chapter": 2,
         "description": "Uncover the traitors who summoned the demons.",
         "objectives": ["Infiltrate the Shadow Council", "Gather evidence",
                        "Confront the traitor"],
         "boss_name": "Shadow Council Leader", "reward_gold": 75000,
         "reward_items": ["Shadow Cloak", "Ring of Detection"],
         "required_level": 350},
        {"title": "The Crystal's Power", "chapter": 3,
         "description": "Find and activate the Crystal of Issavi to seal the portal.",
         "objectives": ["Navigate the Ancient Temple", "Solve the Crystal Puzzle",
                        "Defeat the Final Guardian"],
         "boss_name": "Demon Lord Azazoth", "reward_gold": 150000,
         "reward_items": ["Crystal of Issavi", "Legendary Guard Armor"],
         "required_level": 400},
    ],
    "default": [
        {"title": "A New Beginning", "chapter": 1,
         "description": "Arrive at the starting town and learn the basics.",
         "objectives": ["Talk to the Elder", "Complete training"],
         "boss_name": "", "reward_gold": 1000,
         "reward_items": ["Starter Sword", "Basic Shield"],
         "required_level": 1},
        {"title": "The Rising Threat", "chapter": 2,
         "description": "A dark force threatens the peaceful town.",
         "objectives": ["Investigate the disturbance", "Defeat the bandits",
                        "Find the source of evil"],
         "boss_name": "Bandit King", "reward_gold": 5000,
         "reward_items": ["Iron Shield", "Health Potion x10"],
         "required_level": 20},
        {"title": "The Final Confrontation", "chapter": 3,
         "description": "Face the ultimate evil threatening the realm.",
         "objectives": ["Gather the ancient artifacts", "Enter the Dark Fortress",
                        "Defeat the Dark Lord"],
         "boss_name": "Dark Lord Malachar", "reward_gold": 50000,
         "reward_items": ["Sword of Light", "Crown of the Realm"],
         "required_level": 100},
    ],
}


class StoryGenerator:
    """Generates story arcs for a campaign."""

    def __init__(self, seed: int = 42):
        self._seed = seed

    def generate(self, theme: str = "default",
                 level_range: tuple = (1, 100),
                 side_quests: bool = True) -> List[StoryArc]:
        """
        Generate story arcs for a theme.

        Args:
            theme: Campaign theme.
            level_range: (min_level, max_level) for the campaign.
            side_quests: Whether to include side quest arcs.

        Returns:
            List of StoryArc objects.
        """
        templates = STORY_ARCS.get(theme, STORY_ARCS["default"])
        arcs: List[StoryArc] = []

        min_level, max_level = level_range
        level_span = max_level - min_level

        for template in templates:
            # Scale level requirements to the range
            base_level = template.get("required_level", 1)
            scaled = min_level + int(level_span * (base_level / max(base_level, 100)))

            arc = StoryArc(
                title=template["title"],
                chapter=template["chapter"],
                description=template["description"],
                objectives=list(template["objectives"]),
                boss_name=template["boss_name"],
                reward_gold=template["reward_gold"],
                reward_items=list(template["reward_items"]),
                required_level=max(min_level, min(scaled, max_level)),
                is_main_story=True,
            )
            arcs.append(arc)

        if side_quests:
            side = self._generate_side_quests(theme, level_range, len(arcs))
            arcs.extend(side)

        return arcs

    def _generate_side_quests(self, theme: str,
                              level_range: tuple,
                              start_chapter: int) -> List[StoryArc]:
        """Generate side quest arcs."""
        min_level, max_level = level_range
        mid_level = (min_level + max_level) // 2

        side_templates = [
            {"title": "Lost Treasures of the Ancients",
             "description": "Search for forgotten treasures in ancient ruins.",
             "objectives": ["Find the map", "Navigate the ruins", "Claim the treasure"],
             "boss_name": "Guardian Golem", "reward_gold": 20000},
            {"title": "The Merchant's Plight",
             "description": "Help a merchant recover stolen goods from bandits.",
             "objectives": ["Find the merchant", "Track the bandits", "Recover the goods"],
             "boss_name": "", "reward_gold": 10000},
            {"title": "Cursed Relics",
             "description": "Destroy cursed artifacts spreading corruption.",
             "objectives": ["Locate the relics", "Purify or destroy each one"],
             "boss_name": "Cursed Spirit", "reward_gold": 30000},
        ]

        arcs: List[StoryArc] = []
        for i, st in enumerate(side_templates):
            arc = StoryArc(
                title=st["title"],
                chapter=start_chapter + i + 1,
                description=st["description"],
                objectives=list(st["objectives"]),
                boss_name=st["boss_name"],
                reward_gold=st["reward_gold"],
                required_level=min_level + (mid_level - min_level) * i // 3,
                is_main_story=False,
            )
            arcs.append(arc)

        return arcs

    def generate_main_story(self, theme: str,
                            level_range: tuple = (1, 100)) -> List[StoryArc]:
        """Generate only main story arcs."""
        return self.generate(theme, level_range, side_quests=False)