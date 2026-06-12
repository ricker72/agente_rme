from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class EconomyData:
    """Economy configuration for a campaign."""

    theme: str = ""
    currency_name: str = "Gold"
    base_item_value: int = 100
    price_inflation: float = 1.0
    loot_multiplier: float = 1.0
    supply_cost_multiplier: float = 1.0
    merchant_items: List[Dict[str, Any]] = field(default_factory=list)
    price_ranges: Dict[str, Dict[str, int]] = field(default_factory=dict)
    economic_events: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "theme": self.theme,
            "currency_name": self.currency_name,
            "base_item_value": self.base_item_value,
            "price_inflation": self.price_inflation,
            "loot_multiplier": self.loot_multiplier,
            "supply_cost_multiplier": self.supply_cost_multiplier,
            "merchant_items": self.merchant_items,
            "price_ranges": self.price_ranges,
            "economic_events": self.economic_events,
        }


# Theme-specific economy configs
THEME_ECONOMY: Dict[str, Dict[str, Any]] = {
    "Issavi": {
        "currency_name": "Issavi Gold",
        "base_item_value": 500,
        "price_inflation": 1.5,
        "loot_multiplier": 1.2,
        "supply_cost_multiplier": 1.3,
        "economic_events": [
            "Demon invasion drives up weapon prices",
            "Rare demonic essences flood the market",
            "Black market trades in corrupted artifacts",
        ],
    },
    "Darashia": {
        "currency_name": "Desert Crown",
        "base_item_value": 300,
        "price_inflation": 1.1,
        "loot_multiplier": 0.9,
        "supply_cost_multiplier": 1.2,
        "economic_events": [
            "Sandstorm disrupts trade routes",
            "Ancient treasures discovered in tombs",
            "Water scarcity raises food prices",
        ],
    },
    "Roshamuul": {
        "currency_name": "Soul Shard",
        "base_item_value": 800,
        "price_inflation": 2.0,
        "loot_multiplier": 1.5,
        "supply_cost_multiplier": 1.8,
        "economic_events": [
            "Undead plague destroys farmlands",
            "Curse artifacts command premium prices",
            "Plague doctors charge exorbitant fees",
        ],
    },
    "default": {
        "currency_name": "Gold",
        "base_item_value": 100,
        "price_inflation": 1.0,
        "loot_multiplier": 1.0,
        "supply_cost_multiplier": 1.0,
        "economic_events": [
            "Trade routes stable",
            "Harvest season brings prosperity",
            "Bandit raids disrupt caravans",
        ],
    },
}

# Merchant inventories by tier
MERCHANT_ITEMS_BY_TIER: Dict[str, List[Dict[str, Any]]] = {
    "basic": [
        {"name": "Health Potion", "type": "consumable", "base_price": 50},
        {"name": "Mana Potion", "type": "consumable", "base_price": 75},
        {"name": "Rope", "type": "utility", "base_price": 20},
        {"name": "Torch", "type": "utility", "base_price": 10},
    ],
    "intermediate": [
        {"name": "Steel Sword", "type": "weapon", "base_price": 2000},
        {"name": "Chain Armor", "type": "armor", "base_price": 3000},
        {"name": "Mana Crystal", "type": "consumable", "base_price": 500},
        {"name": "Teleport Scroll", "type": "utility", "base_price": 800},
    ],
    "advanced": [
        {"name": "Enchanted Blade", "type": "weapon", "base_price": 15000},
        {"name": "Dragon Scale Shield", "type": "armor", "base_price": 20000},
        {"name": "Supreme Health Potion", "type": "consumable", "base_price": 2000},
        {"name": "Ring of Power", "type": "accessory", "base_price": 25000},
    ],
}


class EconomyGenerator:
    """Generates economy data for a campaign."""

    def __init__(self, seed: int = 42):
        self._seed = seed

    def generate(
        self, theme: str = "default", level_range: tuple = (1, 100)
    ) -> EconomyData:
        """
        Generate economy data for a theme and level range.

        Args:
            theme: Campaign theme.
            level_range: (min_level, max_level).

        Returns:
            EconomyData with pricing and market data.
        """
        config = THEME_ECONOMY.get(theme, THEME_ECONOMY["default"])
        min_level, max_level = level_range

        # Scale prices by level range
        level_factor = max(1.0, max_level / 100)

        economy = EconomyData(
            theme=theme,
            currency_name=config["currency_name"],
            base_item_value=int(config["base_item_value"] * level_factor),
            price_inflation=config["price_inflation"],
            loot_multiplier=config["loot_multiplier"],
            supply_cost_multiplier=config["supply_cost_multiplier"],
            economic_events=list(config["economic_events"]),
        )

        # Generate price ranges based on level
        economy.price_ranges = {
            "consumables": {
                "min": int(50 * level_factor),
                "max": int(5000 * level_factor),
            },
            "weapons": {
                "min": int(200 * level_factor),
                "max": int(50000 * level_factor),
            },
            "armor": {
                "min": int(300 * level_factor),
                "max": int(60000 * level_factor),
            },
            "accessories": {
                "min": int(1000 * level_factor),
                "max": int(100000 * level_factor),
            },
        }

        # Generate merchant inventory
        if max_level < 50:
            tier = "basic"
        elif max_level < 200:
            tier = "intermediate"
        else:
            tier = "advanced"

        base_items = MERCHANT_ITEMS_BY_TIER[tier]
        economy.merchant_items = []
        for item in base_items:
            adjusted_price = int(
                item["base_price"] * level_factor * config["price_inflation"]
            )
            economy.merchant_items.append(
                {
                    "name": item["name"],
                    "type": item["type"],
                    "price": adjusted_price,
                    "stock": 10,
                }
            )

        return economy

    def calculate_profit(self, economy: EconomyData, base_profit: int) -> int:
        """Calculate adjusted profit based on economy."""
        return int(base_profit * economy.loot_multiplier / economy.price_inflation)

    def calculate_supply_cost(self, economy: EconomyData, base_cost: int) -> int:
        """Calculate adjusted supply cost based on economy."""
        return int(base_cost * economy.supply_cost_multiplier)
