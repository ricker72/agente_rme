from __future__ import annotations

from typing import Dict, List


class RewardDesigner:
    def generate(self, theme: str, progression: Dict[str, object]) -> Dict[str, object]:
        return {
            "items": [
                {"name": f"{theme} Blade", "type": "weapon"},
                {"name": f"{theme} Shield", "type": "armor"},
            ],
            "outfits": [f"{theme} Champion", f"{theme} Warlock"],
            "mounts": [f"{theme} Steed", f"{theme} Drake"],
            "titles": ["Guardian of the Realm", "Abyss Walker"],
            "achievements": [
                "Conqueror of the Depths",
                "Master of the {theme} Saga",
            ],
            "progression_boosts": progression.get("tiers", []),
        }
