from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Faction:
    """A faction in the campaign world."""

    name: str = ""
    alignment: str = ""  # "good", "evil", "neutral", "chaotic"
    description: str = ""
    leader: str = ""
    member_count: int = 100
    primary_color: str = ""
    enemy_factions: List[str] = field(default_factory=list)
    allied_factions: List[str] = field(default_factory=list)
    capital: str = ""
    specialities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "alignment": self.alignment,
            "description": self.description,
            "leader": self.leader,
            "member_count": self.member_count,
            "primary_color": self.primary_color,
            "enemy_factions": self.enemy_factions,
            "allied_factions": self.allied_factions,
            "capital": self.capital,
            "specialities": self.specialities,
        }


FACTION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "Issavi": [
        {
            "name": "The Crimson Guard",
            "alignment": "good",
            "description": "Elite defenders of Issavi, sworn to reclaim the city.",
            "primary_color": "red",
            "specialities": ["melee", "defense"],
            "capital": "Issavi Outpost",
        },
        {
            "name": "Shadow Council",
            "alignment": "evil",
            "description": "Secret cabal that summoned the demons to Issavi.",
            "primary_color": "purple",
            "specialities": ["magic", "deception"],
            "capital": "Hidden Sanctum",
        },
        {
            "name": "Merchant Coalition",
            "alignment": "neutral",
            "description": "Traders who profit from both sides of the conflict.",
            "primary_color": "gold",
            "specialities": ["trade", "crafting"],
            "capital": "Trade District",
        },
    ],
    "Darashia": [
        {
            "name": "Desert Hawks",
            "alignment": "good",
            "description": "Nomadic warriors protecting Darashia's people.",
            "primary_color": "brown",
            "specialities": ["archery", "survival"],
            "capital": "Oasis Camp",
        },
        {
            "name": "Sand Wraiths",
            "alignment": "evil",
            "description": "Undead legion serving the ancient Pharaoh.",
            "primary_color": "black",
            "specialities": ["necromancy", "sand"],
            "capital": "Tomb of Kings",
        },
    ],
    "Roshamuul": [
        {
            "name": "Order of Dawn",
            "alignment": "good",
            "description": "Last bastion of light on the cursed isle.",
            "primary_color": "white",
            "specialities": ["holy", "healing"],
            "capital": "Dawn Fortress",
        },
        {
            "name": "Plague Reapers",
            "alignment": "evil",
            "description": "Cult spreading the undeath plague across Roshamuul.",
            "primary_color": "green",
            "specialities": ["disease", "poison"],
            "capital": "Blight Tower",
        },
    ],
    "default": [
        {
            "name": "The Iron Brotherhood",
            "alignment": "good",
            "description": "Warriors bound by honor to protect the innocent.",
            "primary_color": "silver",
            "specialities": ["combat", "strategy"],
            "capital": "Iron Hold",
        },
        {
            "name": "The Void Collective",
            "alignment": "evil",
            "description": "Servants of the void seeking to unmake reality.",
            "primary_color": "dark",
            "specialities": ["dark magic", "corruption"],
            "capital": "Void Nexus",
        },
        {
            "name": "Wanderers' Pact",
            "alignment": "neutral",
            "description": "A loose alliance of travelers and explorers.",
            "primary_color": "green",
            "specialities": ["exploration", "trade"],
            "capital": "Crossroads Inn",
        },
    ],
}


class FactionGenerator:
    """Generates factions for a campaign with relationships and specialities."""

    def __init__(self, seed: int = 42):
        self._seed = seed

    def generate(self, theme: str = "default", count: int = 3) -> List[Faction]:
        """
        Generate factions for a theme.

        Args:
            theme: Campaign theme.
            count: Number of factions to generate.

        Returns:
            List of Faction objects with relationships.
        """
        templates = FACTION_TEMPLATES.get(theme, FACTION_TEMPLATES["default"])
        factions: List[Faction] = []

        for i in range(min(count, len(templates))):
            t = templates[i]
            faction = Faction(
                name=t["name"],
                alignment=t["alignment"],
                description=t["description"],
                primary_color=t["primary_color"],
                specialities=list(t["specialities"]),
                capital=t["capital"],
                leader=f"Leader of {t['name']}",
                member_count=100 + i * 50,
            )
            factions.append(faction)

        # Generate more if needed beyond templates
        for i in range(len(factions), count):
            alignment = ["good", "evil", "neutral"][i % 3]
            faction = Faction(
                name=f"Generated Faction {i}",
                alignment=alignment,
                description=f"A {alignment} faction in the {theme} region.",
                primary_color=["blue", "red", "green"][i % 3],
                specialities=["combat"],
                capital=f"Base {i}",
                leader=f"Leader {i}",
                member_count=100,
            )
            factions.append(faction)

        # Set up relationships
        self._set_relationships(factions)

        return factions

    def _set_relationships(self, factions: List[Faction]) -> None:
        """Set enemy and ally relationships between factions."""
        for i, f1 in enumerate(factions):
            for j, f2 in enumerate(factions):
                if i >= j:
                    continue
                if f1.alignment == f2.alignment:
                    f1.allied_factions.append(f2.name)
                    f2.allied_factions.append(f1.name)
                elif f1.alignment != "neutral" and f2.alignment != "neutral":
                    f1.enemy_factions.append(f2.name)
                    f2.enemy_factions.append(f1.name)
