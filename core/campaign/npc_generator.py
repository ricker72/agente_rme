from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NPC:
    """A non-player character in the campaign."""
    name: str = ""
    role: str = ""  # "quest_giver", "merchant", "ally", "enemy", "neutral"
    faction: str = ""
    location: str = ""
    dialogue_greeting: str = ""
    dialogue_farewell: str = ""
    quest_ids: List[str] = field(default_factory=list)
    combat_level: int = 1
    is_boss: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "role": self.role, "faction": self.faction,
            "location": self.location, "dialogue_greeting": self.dialogue_greeting,
            "dialogue_farewell": self.dialogue_farewell,
            "quest_ids": self.quest_ids, "combat_level": self.combat_level,
            "is_boss": self.is_boss,
        }


NPC_NAMES_BY_ROLE: Dict[str, List[str]] = {
    "quest_giver": ["Elder Theron", "Captain Lyra", "Scholar Voss", "Healer Miriel",
                     "Scout Renna", "Commander Draven", "Sage Altheris", "Mayor Corbin"],
    "merchant": ["Trader Zara", "Merchant Grix", "Peddler Nysta", "Blacksmith Orren",
                  "Alchemist Fez", "Armorer Krell"],
    "ally": ["Warrior Sera", "Ranger Finn", "Mage Celestia", "Paladin Aldric",
              "Rogue Vex", "Healer Thessa"],
    "enemy": ["Warlord Krazath", "Sorceress Nyx", "Commander Vexul", "Beast Tamer Grul",
               "Necromancer Zethis", "Assassin Shade"],
    "neutral": ["Bartender Max", "Innkeeper Helga", "Guard Captain Brom",
                 "Fisherman Old Tom", "Wanderer Nyssa"],
}

GREETINGS: Dict[str, List[str]] = {
    "quest_giver": ["Greetings, adventurer. I need your help.",
                     "Brave one, come closer. I have a task for you.",
                     "Thank the gods you're here! We need assistance."],
    "merchant": ["Welcome! Browse my wares, all top quality.",
                  "Looking to buy or sell? I've got what you need.",
                  "Finest goods in all of {location}!"],
    "ally": ["I'll fight beside you, friend.",
              "We stand together against the darkness.",
              "Ready when you are, partner."],
    "enemy": ["You dare enter my domain?",
               "Your journey ends here, fool.",
               "Prepare to face your doom!"],
    "neutral": ["Hmm? Oh, hello there.",
                 "Nice weather we're having... considering everything.",
                 "If you need information, talk to someone important."],
}


class NPCGenerator:
    """Generates NPCs for a campaign with roles, dialogue, and faction alignment."""

    def __init__(self, seed: int = 42):
        self._seed = seed
        self._used_names: set = set()

    def generate(self, theme: str = "default",
                 faction_names: Optional[List[str]] = None,
                 count: int = 8,
                 locations: Optional[List[str]] = None) -> List[NPC]:
        """Generate a set of NPCs for the campaign."""
        faction_names = faction_names or []
        locations = locations or ["Town Center"]
        npcs: List[NPC] = []
        roles = ["quest_giver", "merchant", "ally", "enemy", "neutral"]

        for i in range(count):
            role = roles[i % len(roles)]
            faction = faction_names[i % len(faction_names)] if faction_names else ""
            location = locations[i % len(locations)]
            npc = self._create_npc(role, faction, location, i)
            npcs.append(npc)

        return npcs

    def _create_npc(self, role: str, faction: str,
                    location: str, index: int) -> NPC:
        names = NPC_NAMES_BY_ROLE.get(role, NPC_NAMES_BY_ROLE["neutral"])
        name = names[index % len(names)]
        if name in self._used_names:
            name = f"{name} the {index}"
        self._used_names.add(name)

        greetings = GREETINGS.get(role, GREETINGS["neutral"])
        greeting = greetings[index % len(greetings)].replace("{location}", location)

        farewell_templates = ["Farewell, adventurer.", "May the gods protect you.",
                              "Be safe out there.", "Until we meet again."]
        farewell = farewell_templates[index % len(farewell_templates)]

        level = 1
        if role == "enemy":
            level = 100 + index * 50
        elif role == "ally":
            level = 80 + index * 30
        elif role == "merchant":
            level = 1

        return NPC(
            name=name, role=role, faction=faction, location=location,
            dialogue_greeting=greeting, dialogue_farewell=farewell,
            combat_level=level, is_boss=(role == "enemy" and index > 3),
        )

    def generate_boss(self, name: str, faction: str,
                      location: str, level: int = 300) -> NPC:
        """Generate a single boss NPC."""
        return NPC(
            name=name, role="enemy", faction=faction, location=location,
            dialogue_greeting=f"YOU DARE CHALLENGE ME, MORTAL? I AM {name.upper()}!",
            dialogue_farewell="This... cannot be...",
            combat_level=level, is_boss=True,
        )