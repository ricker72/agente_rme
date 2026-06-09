from __future__ import annotations

from typing import Dict


class BossDesigner:
    def design(self, theme: str, difficulty: str, index: int) -> Dict[str, object]:
        arena = f"{theme} Arena {index}"
        mechanics = [
            "phase-based attacks",
            "environmental hazards",
            "summon adds",
        ]
        loot = [
            {"item": f"{theme} Relic", "rarity": "epic"},
            {"item": f"{theme} Essence", "rarity": "rare"},
        ]
        return {
            "name": f"{theme} Warlord {index}",
            "arena": arena,
            "mechanics": mechanics,
            "loot": loot,
            "difficulty": difficulty,
            "cooldown": f"{24 + index * 6}h",
        }
