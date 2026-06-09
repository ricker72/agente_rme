from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LoreEntry:
    """A single piece of campaign lore."""
    title: str = ""
    category: str = ""  # "history", "myth", "legend", "prophecy", "secret"
    content: str = ""
    importance: int = 1  # 1-5
    related_factions: List[str] = field(default_factory=list)
    related_npcs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "category": self.category,
            "content": self.content,
            "importance": self.importance,
            "related_factions": self.related_factions,
            "related_npcs": self.related_npcs,
        }


# Theme-based lore templates
THEME_LORE: Dict[str, List[Dict[str, str]]] = {
    "Issavi": [
        {"title": "The Fall of Issavi", "category": "history",
         "content": "Once a thriving city, Issavi fell to a demonic invasion "
                    "that corrupted its ancient temples and markets.",
         "importance": 5},
        {"title": "The Crystal of Issavi", "category": "myth",
         "content": "Legends speak of a crystal hidden beneath the city that "
                    "can seal the demonic portal forever.",
         "importance": 4},
        {"title": "The Last Stand of the Issavi Guard", "category": "legend",
         "content": "Captain Thalor led the final defense of the city gates, "
                    "buying time for civilians to escape.",
         "importance": 3},
    ],
    "Darashia": [
        {"title": "The Desert's Secret", "category": "history",
         "content": "Beneath Darashia's dunes lies an ancient civilization "
                    "with technology far beyond our understanding.",
         "importance": 4},
        {"title": "The Scarab Curse", "category": "myth",
         "content": "Those who disturb the Pharaoh's tomb are cursed with "
                    "eternal thirst and wandering in the desert.",
         "importance": 3},
    ],
    "Roshamuul": [
        {"title": "The Cursed Isle", "category": "history",
         "content": "Roshamuul was once a prosperous trading hub until a "
                    "plague of undeath consumed its population.",
         "importance": 5},
        {"title": "The Blood Moon Prophecy", "category": "prophecy",
         "content": "When the moon turns crimson, the dead shall rise and "
                    "the living shall face their final reckoning.",
         "importance": 5},
    ],
    "default": [
        {"title": "The Age of Chaos", "category": "history",
         "content": "In the beginning, the world was formless and chaotic. "
                    "The gods shaped the lands and populated them with life.",
         "importance": 3},
        {"title": "The Great Schism", "category": "legend",
         "content": "When the gods disagreed, the world split into realms "
                    "of light and shadow, each claiming their followers.",
         "importance": 4},
    ],
}

# Faction-specific lore
FACTION_LORE_TEMPLATES: Dict[str, List[str]] = [
    "{faction} traces its origins to the first settlers who braved "
    "the wilds and carved civilization from the wilderness.",
    "The {faction} once controlled all trade routes, but their monopoly "
    "was broken when rival factions formed alliances.",
    "Members of the {faction} swear an oath upon admission to protect "
    "the secrets of their order until death.",
    "The {faction} maintains neutrality in most conflicts, but when "
    "threatened, they reveal their formidable military might.",
]


class LoreGenerator:
    """
    Generates campaign lore based on theme and factions.

    Produces history entries, myths, legends, and prophecies
    that form the narrative backbone of a campaign.
    """

    def __init__(self, seed: int = 42):
        self._seed = seed
        self._counter = 0

    def _next_id(self) -> int:
        self._counter += 1
        return self._counter

    def generate(self, theme: str = "default",
                 faction_names: Optional[List[str]] = None,
                 count: int = 5) -> List[LoreEntry]:
        """
        Generate lore entries for a theme.

        Args:
            theme: Campaign theme (e.g. "Issavi", "Darashia").
            faction_names: List of faction names for related lore.
            count: Number of lore entries to generate.

        Returns:
            List of LoreEntry objects.
        """
        faction_names = faction_names or []
        entries: List[LoreEntry] = []

        # Theme-based lore
        templates = THEME_LORE.get(theme, THEME_LORE["default"])
        for template in templates[:count]:
            entry = LoreEntry(
                title=template["title"],
                category=template["category"],
                content=template["content"],
                importance=template["importance"],
                related_factions=faction_names[:2] if faction_names else [],
            )
            entries.append(entry)

        # Faction-specific lore
        remaining = count - len(entries)
        for i in range(remaining):
            template = FACTION_LORE_TEMPLATES[i % len(FACTION_LORE_TEMPLATES)]
            faction = faction_names[i % len(faction_names)] if faction_names else "The Order"
            content = template.format(faction=faction)
            entries.append(LoreEntry(
                title=f"The Story of {faction} - Part {i + 1}",
                category="history",
                content=content,
                importance=2 + (i % 3),
                related_factions=[faction],
            ))

        return entries[:count]

    def generate_prophecy(self, theme: str,
                          factions: Optional[List[str]] = None) -> LoreEntry:
        """Generate a single prophecy entry."""
        faction_text = " and ".join(factions[:2]) if factions else "the chosen ones"
        return LoreEntry(
            title=f"The Prophecy of {theme}",
            category="prophecy",
            content=f"In the darkest hour, {faction_text} shall rise to "
                    f"confront the ancient evil lurking within {theme}. "
                    f"Only through unity can the world be saved from "
                    f"eternal darkness.",
            importance=5,
            related_factions=factions or [],
        )

    def generate_secret(self, theme: str,
                        npc_name: Optional[str] = None) -> LoreEntry:
        """Generate a hidden secret entry."""
        npc_text = f"discovered by {npc_name}" if npc_name else "hidden in ancient texts"
        return LoreEntry(
            title=f"Secret of {theme}",
            category="secret",
            content=f"A forgotten truth {npc_text}: beneath {theme} lies "
                    f"a sealed chamber containing power that could either "
                    f"save or destroy the world.",
            importance=4,
            related_npcs=[npc_name] if npc_name else [],
        )