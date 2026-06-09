from __future__ import annotations

from typing import Dict, List


class EconomyDesigner:
    def balance(self, theme: str, content: Dict[str, object]) -> Dict[str, object]:
        return {
            "gold": self._gold_profile(theme, content),
            "loot": self._loot_balance(content),
            "rares": self._rare_distribution(content),
            "crafting": self._crafting_flow(theme),
            "consumables": self._consumable_prices(theme),
        }

    def _gold_profile(self, theme: str, content: Dict[str, object]) -> Dict[str, object]:
        return {
            "entry_reward": 500,
            "midgame_reward": 1800,
            "endgame_reward": 7200,
            "trade_goods": [f"{theme} Ore", f"{theme} Silk"],
        }

    def _loot_balance(self, content: Dict[str, object]) -> Dict[str, object]:
        return {
            "common": 0.6,
            "uncommon": 0.25,
            "rare": 0.1,
            "legendary": 0.05,
        }

    def _rare_distribution(self, content: Dict[str, object]) -> List[Dict[str, object]]:
        bosses = content.get("bosses", [])
        return [
            {"boss": boss.get("name"), "drop": "legendary relic"}
            for boss in bosses[:3]
        ]

    def _crafting_flow(self, theme: str) -> Dict[str, object]:
        return {
            "materials": [f"{theme} Shard", f"{theme} Essence"],
            "recipes": ["weapon upgrade", "armor polish"],
        }

    def _consumable_prices(self, theme: str) -> Dict[str, int]:
        return {
            "health_potion": 45,
            "mana_potion": 55,
            "stamina_food": 30,
        }
