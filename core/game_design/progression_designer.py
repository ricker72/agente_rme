from __future__ import annotations

from typing import Dict


class ProgressionDesigner:
    TIERS = [
        ("Tier 1", "1-50"),
        ("Tier 2", "50-100"),
        ("Tier 3", "100-200"),
        ("Tier 4", "200-300"),
        ("Tier 5", "300-500"),
        ("Endgame", "500+"),
    ]

    def distribute(self) -> Dict[str, object]:
        tiers = []
        for name, range_text in self.TIERS:
            tiers.append(
                {
                    "name": name,
                    "recommended_level": range_text,
                    "difficulty": self._difficulty_for_tier(name),
                    "progression_goal": self._goal_for_tier(name),
                }
            )
        return {
            "tiers": tiers,
            "summary": "A structured progression from starter to endgame content.",
        }

    def _difficulty_for_tier(self, tier: str) -> str:
        mapping = {
            "Tier 1": "easy",
            "Tier 2": "moderate",
            "Tier 3": "challenging",
            "Tier 4": "hard",
            "Tier 5": "deadly",
            "Endgame": "legendary",
        }
        return mapping.get(tier, "moderate")

    def _goal_for_tier(self, tier: str) -> str:
        goals = {
            "Tier 1": "Establish safe paths and early story hooks.",
            "Tier 2": "Introduce new gear and hunt locations.",
            "Tier 3": "Raise the threat and unlock deeper dungeons.",
            "Tier 4": "Challenge the player with complex encounters.",
            "Tier 5": "Deliver endgame raid content.",
            "Endgame": "Reward mastery with legendary achievements.",
        }
        return goals.get(tier, "Advance player progression.")
