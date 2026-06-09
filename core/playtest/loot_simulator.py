"""
Loot Simulator — Calculates loot yield per hour for hunt areas.

Simulates loot drops based on monster types, kill rates, and loot tables.
Provides gold per hour, item drops, and loot efficiency metrics.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class LootDrop:
    """A single loot drop event."""
    item_name: str
    item_id: int
    gold: int
    count: int


@dataclass
class LootReport:
    """Aggregated loot statistics from simulation."""
    total_gold: int
    gold_per_hour: float
    total_items: int
    items_per_hour: float
    total_kills: int
    gold_per_kill: float
    item_drops: Dict[str, int]  # item_name -> count
    best_vocation_gold: str
    best_vocation_items: str
    loot_efficiency: float  # gold / time ratio
    rare_drops: List[str]


@dataclass
class LootTable:
    """Loot table for a monster type."""
    monster_name: str
    gold_min: int
    gold_max: int
    items: List[Tuple[str, int, float]]  # (name, chance_per_kill_%, item_id)
    rare_items: List[Tuple[str, int, float]]  # < 1% drop chance


# ── Common Loot Tables ──

COMMON_LOOT_TABLES: Dict[str, LootTable] = {
    "Dragon": LootTable(
        monster_name="Dragon",
        gold_min=150, gold_max=400,
        items=[
            ("Gold Coin", 100, 3031),
            ("Dragon Ham", 80, 11451),
            ("Plate Armor", 5, 3366),
            ("Magic Plate Armor", 0.5, 3366),
        ],
        rare_items=[
            ("Magic Plate Armor", 0.5, 3366),
        ],
    ),
    "Hydra": LootTable(
        monster_name="Hydra",
        gold_min=300, gold_max=800,
        items=[
            ("Gold Coin", 100, 3031),
            ("Green Dragon Leather", 40, 5893),
            ("Small Emerald", 15, 3083),
            ("Plate Armor", 3, 3366),
        ],
        rare_items=[
            ("Small Emerald", 15, 3083),
        ],
    ),
    "Demon": LootTable(
        monster_name="Demon",
        gold_min=500, gold_max=1200,
        items=[
            ("Gold Coin", 100, 3031),
            ("Demon Helmet", 2, 3168),
            ("Demon Shield", 1.5, 3122),
            ("Magic Plate Armor", 0.3, 3366),
            ("Red Gem", 5, 3032),
        ],
        rare_items=[
            ("Demon Helmet", 2, 3168),
            ("Demon Shield", 1.5, 3122),
            ("Magic Plate Armor", 0.3, 3366),
        ],
    ),
    "Rat": LootTable(
        monster_name="Rat",
        gold_min=5, gold_max=15,
        items=[
            ("Gold Coin", 100, 3031),
            ("Cheese", 30, 2696),
        ],
        rare_items=[],
    ),
    "Rotworm": LootTable(
        monster_name="Rotworm",
        gold_min=15, gold_max=40,
        items=[
            ("Gold Coin", 100, 3031),
            ("Meat", 50, 2681),
            ("Plate Armor", 1, 3366),
        ],
        rare_items=[],
    ),
    "Goblin": LootTable(
        monster_name="Goblin",
        gold_min=20, gold_max=60,
        items=[
            ("Gold Coin", 100, 3031),
            ("Short Sword", 15, 3294),
            ("Leather Armor", 10, 3355),
        ],
        rare_items=[],
    ),
    "Orc Shaman": LootTable(
        monster_name="Orc Shaman",
        gold_min=80, gold_max=200,
        items=[
            ("Gold Coin", 100, 3031),
            ("Staff", 10, 3210),
            ("Orb", 3, 3051),
        ],
        rare_items=[
            ("Orb", 3, 3051),
        ],
    ),
    "Minotaur": LootTable(
        monster_name="Minotaur",
        gold_min=30, gold_max=100,
        items=[
            ("Gold Coin", 100, 3031),
            ("Minotaur Axe", 5, 3318),
            ("Chain Armor", 8, 3358),
        ],
        rare_items=[
            ("Minotaur Axe", 5, 3318),
        ],
    ),
    "Vampire": LootTable(
        monster_name="Vampire",
        gold_min=100, gold_max=300,
        items=[
            ("Gold Coin", 100, 3031),
            ("Vampire Shield", 3, 3116),
            ("Plate Armor", 5, 3366),
            ("Blood Tainted", 1, 9634),
        ],
        rare_items=[
            ("Vampire Shield", 3, 3116),
        ],
    ),
    "Behemoth": LootTable(
        monster_name="Behemoth",
        gold_min=800, gold_max=2000,
        items=[
            ("Gold Coin", 100, 3031),
            ("Magic Plate Armor", 1, 3366),
            ("Behemoth Axe", 0.8, 3344),
            ("Golden Armor", 0.3, 3360),
        ],
        rare_items=[
            ("Magic Plate Armor", 1, 3366),
            ("Golden Armor", 0.3, 3360),
        ],
    ),
    "Grim Reaper": LootTable(
        monster_name="Grim Reaper",
        gold_min=1000, gold_max=3000,
        items=[
            ("Gold Coin", 100, 3031),
            ("Magic Plate Armor", 1.5, 3366),
            ("Scythe", 0.5, 3334),
            ("Blessed Sponge", 0.1, 6499),
        ],
        rare_items=[
            ("Blessed Sponge", 0.1, 6499),
        ],
    ),
}


class LootSimulator:
    """Simulates loot drops over a hunt session."""

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._tables: Dict[str, LootTable] = dict(COMMON_LOOT_TABLES)

    def register_loot_table(self, table: LootTable) -> None:
        """Register a custom loot table for a monster."""
        self._tables[table.monster_name] = table

    def get_loot_table(self, monster_name: str) -> Optional[LootTable]:
        """Get the loot table for a monster."""
        return self._tables.get(monster_name)

    def simulate_drop(self, table: LootTable) -> LootDrop:
        """Simulate a single loot drop from a monster."""
        gold = self._rng.randint(table.gold_min, table.gold_max)
        items_dropped: List[Tuple[str, int]] = []
        rare: List[str] = []

        # Check regular items
        for item_name, chance, item_id in table.items:
            if self._rng.random() * 100 < chance:
                count = self._rng.randint(1, 3)
                items_dropped.append((item_name, count))

        # Check rare items (< 1% chance)
        for item_name, chance, item_id in table.rare_items:
            if self._rng.random() * 100 < chance:
                items_dropped.append((item_name, 1))
                rare.append(item_name)

        total_items = sum(c for _, c in items_dropped)
        best_name = items_dropped[0][0] if items_dropped else "Gold Coin"
        best_id = 3031  # Gold Coin default

        for name, _ in items_dropped:
            for t_name, _, t_id in table.items + table.rare_items:
                if t_name == name:
                    best_id = t_id
                    break

        return LootDrop(
            item_name=best_name,
            item_id=best_id,
            gold=gold,
            count=total_items,
        )

    def simulate_hunt(
        self,
        monster_name: str,
        kills: int,
    ) -> Tuple[int, Dict[str, int], List[str]]:
        """
        Simulate loot from killing N monsters.

        Returns:
            (total_gold, {item_name: count}, [rare_drops])
        """
        table = self._tables.get(monster_name)
        if table is None:
            # Fallback: just gold
            total_gold = kills * 50
            return total_gold, {}, []

        total_gold = 0
        item_counts: Dict[str, int] = {}
        rare_drops: List[str] = []

        for _ in range(kills):
            drop = self.simulate_drop(table)
            total_gold += drop.gold
            # Simulate item drops from the table
            for item_name, chance, item_id in table.items:
                if self._rng.random() * 100 < chance:
                    count = self._rng.randint(1, 3)
                    item_counts[item_name] = item_counts.get(item_name, 0) + count
            for item_name, chance, item_id in table.rare_items:
                if self._rng.random() * 100 < chance:
                    item_counts[item_name] = item_counts.get(item_name, 0) + 1
                    rare_drops.append(item_name)

        return total_gold, item_counts, rare_drops

    def simulate_hunt_rotation(
        self,
        monsters: List[str],
        kills_per_monster: int,
        rotation_minutes: float = 60.0,
    ) -> LootReport:
        """
        Simulate loot from a full hunt rotation.

        Args:
            monsters: List of monster names in the hunt
            kills_per_monster: Expected kills per monster type per rotation
            rotation_minutes: Duration of the rotation

        Returns:
            LootReport with aggregated loot statistics
        """
        total_gold = 0
        total_items = 0
        all_item_counts: Dict[str, int] = {}
        all_rare: List[str] = []
        total_kills = 0

        for monster_name in monsters:
            gold, items, rare = self.simulate_hunt(monster_name, kills_per_monster)
            total_gold += gold
            total_kills += kills_per_monster
            for item_name, count in items.items():
                all_item_counts[item_name] = all_item_counts.get(item_name, 0) + count
                total_items += count
            all_rare.extend(rare)

        rotation_seconds = rotation_minutes * 60.0
        gold_per_hour = (total_gold / max(rotation_seconds, 1.0)) * 3600.0
        items_per_hour = (total_items / max(rotation_seconds, 1.0)) * 3600.0
        gold_per_kill = total_gold / max(total_kills, 1)
        loot_efficiency = gold_per_hour / 1000.0  # normalize to k/hr

        return LootReport(
            total_gold=total_gold,
            gold_per_hour=gold_per_hour,
            total_items=total_items,
            items_per_hour=items_per_hour,
            total_kills=total_kills,
            gold_per_kill=gold_per_kill,
            item_drops=all_item_counts,
            best_vocation_gold="knight",  # placeholder, computed externally
            best_vocation_items="sorcerer",  # placeholder
            loot_efficiency=loot_efficiency,
            rare_drops=all_rare,
        )

    def compare_vocation_loot(
        self,
        monsters: List[str],
        kills_per_monster: int,
        vocation_kill_rates: Dict[str, float],
    ) -> Dict[str, LootReport]:
        """
        Compare loot across vocations based on their kill rate multiplier.

        Args:
            monsters: Monster names in the hunt
            kills_per_monster: Base kills per monster
            vocation_kill_rates: {vocation: kill_rate_multiplier}
        """
        reports = {}
        for vocation, multiplier in vocation_kill_rates.items():
            adjusted_kills = int(kills_per_monster * multiplier)
            reports[vocation] = self.simulate_hunt_rotation(
                monsters=monsters,
                kills_per_monster=adjusted_kills,
            )
        return reports