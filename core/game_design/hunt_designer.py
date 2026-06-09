from __future__ import annotations

from typing import Dict


class HuntDesigner:
    def design(self, recommended_level: str, theme: str, index: int) -> Dict[str, object]:
        return {
            "name": f"{theme} Hunt {index}",
            "recommended_level": recommended_level,
            "monster_pool": [
                f"{theme} Scout",
                f"{theme} Ravager",
                f"{theme} Warden",
            ],
            "loot_profile": {
                "common": ["gold coins", "healing potion"],
                "rare": [f"{theme} Essence", f"{theme} Claw"],
                "epic": [f"{theme} Trophy"],
            },
            "respawn_density": "dense" if index <= 2 else "moderate",
        }
