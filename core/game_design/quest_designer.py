from __future__ import annotations

from typing import Dict


class QuestDesigner:
    def design(self, quest_type: str, theme: str, hook: str) -> Dict[str, object]:
        base_title = {
            "story": f"The {theme} Legacy",
            "exploration": f"Secrets of {theme}",
            "boss": f"Hunt the {theme} Tyrant",
            "collection": f"Gather {theme} Relics",
            "lever": f"Switch of {theme}",
            "puzzle": f"Mysteries Beyond {theme}",
        }.get(quest_type, f"{theme} Quest")
        return {
            "type": quest_type,
            "title": base_title,
            "description": hook,
            "objectives": self._objectives_for_type(quest_type, theme),
            "reward": self._reward_for_type(quest_type),
        }

    def _objectives_for_type(self, quest_type: str, theme: str):
        mapping = {
            "story": [
                f"Meet the lorekeeper in {theme} City",
                "Uncover the first artifact",
            ],
            "exploration": [
                f"Chart three new zones around {theme}",
                "Report back with notes",
            ],
            "boss": ["Defeat the marked boss", "Survive the arena encounter"],
            "collection": ["Collect 10 ancient shards", "Return to the city historian"],
            "lever": ["Activate the hidden lever", "Escape the collapsing chamber"],
            "puzzle": ["Solve the rune sequence", "Open the sealed gate"],
        }
        return mapping.get(quest_type, ["Complete the objective"])

    def _reward_for_type(self, quest_type: str):
        mapping = {
            "story": "experience and lore",
            "exploration": "map fragments and gold",
            "boss": "rare item and reputation",
            "collection": "crafting materials",
            "lever": "access to a hidden vault",
            "puzzle": "ancient artifact",
        }
        return mapping.get(quest_type, "experience")
