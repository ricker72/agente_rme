"""
MapDesigner — Location resolver for content generators.

Wraps WorldModel and AssetRegistry to provide location-based queries
for placing quests, raids, bosses, rewards, and missions.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple

from core.world.world_model import WorldModel
from core.world.structure import Structure
from core.world.region import Region

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Zone definitions: theme → level band and room metadata
# ---------------------------------------------------------------------------

_ZONES: List[Dict[str, Any]] = [
    {"name": "Venore Swamps", "theme": "swamp", "level_min": 1, "level_max": 50},
    {"name": "Thais Plains", "theme": "plains", "level_min": 1, "level_max": 30},
    {"name": "Carlin Forest", "theme": "forest", "level_min": 10, "level_max": 80},
    {"name:": "Kazordoon Depths", "theme": "mountain", "level_min": 50, "level_max": 150},
    {"name": "Ab'Dendriel Jungle", "theme": "jungle", "level_min": 30, "level_max": 120},
    {"name": "Darashia Desert", "theme": "desert", "level_min": 100, "level_max": 250},
    {"name": "Svargrond Tundra", "theme": "tundra", "level_min": 150, "level_max": 300},
    {"name": "Issavi Catacombs", "theme": "catacomb", "level_min": 250, "level_max": 450},
    {"name": "Roshamuul Fortress", "theme": "fortress", "level_min": 350, "level_max": 500},
    {"name": "Feyrist Depths", "theme": "fey", "level_min": 200, "level_max": 400},
    {"name": "Goroma Volcano", "theme": "volcano", "level_min": 80, "level_max": 200},
    {"name": "Monkey Island", "theme": "island", "level_min": 20, "level_max": 60},
]

# Fix the typo in the Kazordoon entry
_ZONES[3]["name"] = "Kazordoon Depths"

# ---------------------------------------------------------------------------
# Boss pool per level band
# ---------------------------------------------------------------------------

_BOSS_POOLS: Dict[str, List[Dict[str, Any]]] = {
    "low": [
        {"name": "Troll Champion", "abilities": ["bash", "smash"]},
        {"name": "Orc Shaman", "abilities": ["fireball", "heal"]},
        {"name": "Goblin Leader", "abilities": ["backstab", "poison"]},
    ],
    "mid": [
        {"name": "Dragon Lord", "abilities": ["fire breath", "tail swipe", "fear"]},
        {"name": "Grim Reaper", "abilities": ["scythe strike", "life drain", "summon wraiths"]},
        {"name": "Werewolf Alpha", "abilities": ["howl", "claw fury", "regenerate"]},
    ],
    "high": [
        {"name": "Dracola", "abilities": ["blood drain", "bat swarm", "charm", "dark aura"]},
        {"name": "Morgaroth", "abilities": ["inferno", "meteor", "summon demons", "hell storm"]},
        {"name": "Orshabaal", "abilities": ["crushing blow", "fire wave", "demon army", "berserk"]},
    ],
    "extreme": [
        {"name": "The Scourge of Oblivion", "abilities": ["void strike", "reality tear", "soul harvest", "dimensional rift", "entropy"]},
        {"name": "Astral Whisper", "abilities": ["mind shatter", "cosmic ray", "phase shift", "gravity well", "astral prison"]},
    ],
}

# ---------------------------------------------------------------------------
# Item reward pools per level band
# ---------------------------------------------------------------------------

_REWARD_POOLS: Dict[str, List[Dict[str, Any]]] = {
    "low": [
        {"name": "Rusty Sword", "rarity": "common", "value": 50},
        {"name": "Leather Armor", "rarity": "common", "value": 80},
        {"name": "Health Potion", "rarity": "common", "value": 25},
    ],
    "mid": [
        {"name": "Magic Plate Armor", "rarity": "rare", "value": 900},
        {"name": "Demon Helmet", "rarity": "rare", "value": 800},
        {"name": "Bright Sword", "rarity": "rare", "value": 600},
        {"name": "Strong Mana Potion", "rarity": "uncommon", "value": 150},
    ],
    "high": [
        {"name": "Demonbone Armor", "rarity": "epic", "value": 5000},
        {"name": "Ravager Axe", "rarity": "epic", "value": 4500},
        {"name": "Blessed Wooden Stake", "rarity": "epic", "value": 3000},
        {"name": "Ultimate Health Potion", "rarity": "rare", "value": 500},
    ],
    "extreme": [
        {"name": "Blade of Corruption", "rarity": "legendary", "value": 20000},
        {"name": "Crown of the Ancients", "rarity": "legendary", "value": 18000},
        {"name": "Staff of Infinite Power", "rarity": "legendary", "value": 25000},
    ],
}

# ---------------------------------------------------------------------------
# Mission objective templates
# ---------------------------------------------------------------------------

_MISSION_TEMPLATES: Dict[str, List[str]] = {
    "exploration": [
        "Discover the hidden chamber in {area}",
        "Map all pathways through {area}",
        "Reach the deepest point of {area}",
    ],
    "rescue": [
        "Locate the captive in {area}",
        "Defeat the guards blocking the exit",
        "Escort the prisoner to safety",
    ],
    "combat": [
        "Defeat {count} enemies in {area}",
        "Survive three waves of attackers",
        "Eliminate the enemy commander",
    ],
    "collection": [
        "Gather {count} ancient relics from {area}",
        "Find 3 sealed artifacts",
        "Return all relics to the quest giver",
    ],
    "escort": [
        "Protect the NPC through {area}",
        "Defeat ambushes along the route",
        "Reach the destination alive",
    ],
    "stealth": [
        "Infiltrate {area} undetected",
        "Retrieve the stolen blueprint",
        "Escape without raising the alarm",
    ],
}

# ---------------------------------------------------------------------------
# Lever / Puzzle room templates
# ---------------------------------------------------------------------------

_LEVER_ROOM_TEMPLATES: List[Dict[str, Any]] = [
    {
        "name": "Flood Gate Lever",
        "description": "Pull the lever to flood the lower passage, revealing hidden treasures.",
        "objectives": ["Locate the rusted lever", "Pull the lever to activate the flood gate", "Collect items from the flooded chamber"],
    },
    {
        "name": "Collapsing Bridge Switch",
        "description": "Activate the switch to extend the bridge over the chasm.",
        "objectives": ["Find the pressure plate", "Activate the bridge mechanism", "Cross before it collapses"],
    },
    {
        "name": "Poison Gas Release",
        "description": "Pull the lever to release toxic gas, weakening the boss ahead.",
        "objectives": ["Locate the valve lever", "Pull the lever to release poison gas", "Engage the weakened boss"],
    },
    {
        "name": "Spinning Blade Room",
        "description": "The lever controls the deadly spinning blades blocking the path.",
        "objectives": ["Dodge the blades to reach the lever", "Pull the lever to stop the blades", "Proceed through the corridor"],
    },
    {
        "name": "Teleporter Activation",
        "description": "Activate the ancient lever to power up the teleporter pad.",
        "objectives": ["Find the energy crystal", "Place the crystal in the lever mechanism", "Step onto the activated teleporter"],
    },
]

_PUZZLE_ROOM_TEMPLATES: List[Dict[str, Any]] = [
    {
        "name": "Rune Sequence Chamber",
        "description": "Ancient runes on the floor must be activated in the correct order.",
        "objectives": ["Examine the hint inscriptions on the walls", "Activate runes in the correct sequence", "Claim the reward from the opened vault"],
    },
    {
        "name": "Elemental Pillar Puzzle",
        "description": "Four elemental pillars must be aligned to unlock the sealed door.",
        "objectives": ["Identify the element of each pillar", "Rotate pillars to match the correct alignment", "Enter the opened chamber"],
    },
    {
        "name": "Mirror Reflection Maze",
        "description": "Redirect the light beam using mirrors to unlock the exit.",
        "objectives": ["Adjust the first mirror angle", "Bounce the beam through all mirrors", "Hit the target crystal to open the gate"],
    },
    {
        "name": "Weight Balance Puzzle",
        "description": "Place the correct weights on the scale to open the passage.",
        "objectives": ["Search the room for weight tokens", "Calculate the correct balance", "Place weights and open the door"],
    },
    {
        "name": "Memory Rune Challenge",
        "description": "Remember and repeat the rune sequence shown at the entrance.",
        "objectives": ["Watch the initial rune sequence carefully", "Repeat the sequence from memory", "Pass through the opened door"],
    },
]


class MapDesigner:
    """
    Resolves world locations for content placement.

    Integrates with WorldModel (structures, regions) and AssetRegistry
    (monsters, items) to provide contextual placement data.
    """

    def __init__(
        self,
        world_model: Optional[WorldModel] = None,
        asset_registry: Optional[Any] = None,
    ):
        self.world_model = world_model
        self.asset_registry = asset_registry

    # ------------------------------------------------------------------
    # Level band helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _level_band(min_level: int) -> str:
        """Classify a minimum level into a band string."""
        if min_level < 80:
            return "low"
        elif min_level < 250:
            return "mid"
        elif min_level < 400:
            return "high"
        return "extreme"

    @staticmethod
    def _deterministic_offset(key: str, mod: int) -> int:
        """Produce a deterministic int from a string key."""
        h = hashlib.sha256(key.encode()).hexdigest()
        return int(h[:8], 16) % mod

    # ------------------------------------------------------------------
    # Zone selection
    # ------------------------------------------------------------------

    def _matching_zones(
        self, min_level: int, max_level: int
    ) -> List[Dict[str, Any]]:
        """Return zones whose level band overlaps the requested range."""
        return [
            z for z in _ZONES
            if z["level_min"] <= max_level and z["level_max"] >= min_level
        ]

    def _pick_zone(
        self, min_level: int, max_level: int, hint: str = ""
    ) -> Dict[str, Any]:
        """Pick a zone deterministically based on level range and hint."""
        zones = self._matching_zones(min_level, max_level)
        if not zones:
            # Fallback: pick closest zone by midpoint
            mid = (min_level + max_level) // 2
            zones = sorted(
                _ZONES,
                key=lambda z: abs((z["level_min"] + z["level_max"]) // 2 - mid),
            )
        key = f"{min_level}:{max_level}:{hint}"
        idx = self._deterministic_offset(key, len(zones))
        return zones[idx]

    # ------------------------------------------------------------------
    # Public API used by generators
    # ------------------------------------------------------------------

    def find_valid_location(
        self, min_level: int, max_level: int
    ) -> str:
        """
        Find a valid named location for a quest within the level range.

        Returns the zone name string.
        """
        zone = self._pick_zone(min_level, max_level, hint="quest")
        return zone["name"]

    def select_raid_zone(
        self, min_level: int, max_level: int
    ) -> str:
        """
        Select a zone appropriate for raid content.

        Returns the zone name string.
        """
        zone = self._pick_zone(min_level, max_level, hint="raid")
        return zone["name"]

    def get_boss_lair(
        self, min_level: int, max_level: int
    ) -> str:
        """
        Find a boss lair location within the level range.

        Returns the zone name string.
        """
        zone = self._pick_zone(min_level, max_level, hint="boss")
        return zone["name"]

    def get_reward_bonus(self, min_level: int) -> int:
        """
        Calculate a location-based gold bonus for rewards.

        Higher level zones give larger bonuses.
        """
        band = self._level_band(min_level)
        bonuses = {"low": 50, "mid": 200, "high": 500, "extreme": 1500}
        return bonuses.get(band, 100)

    def select_mission_area(
        self, min_level: int, max_level: int
    ) -> str:
        """
        Select an area for mission content.

        Returns the zone name string.
        """
        zone = self._pick_zone(min_level, max_level, hint="mission")
        return zone["name"]

    def get_zone_theme(self, zone_name: str) -> str:
        """Get the theme string for a given zone name."""
        for z in _ZONES:
            if z["name"] == zone_name:
                return z["theme"]
        return "dungeon"

    # ------------------------------------------------------------------
    # Boss selection
    # ------------------------------------------------------------------

    def select_boss(
        self, min_level: int, boss_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Select a boss appropriate for the given level.

        Returns a dict with 'name' and 'abilities'.
        """
        band = self._level_band(min_level)
        pool = _BOSS_POOLS.get(band, _BOSS_POOLS["low"])
        key = f"{min_level}:{boss_type or 'default'}"
        idx = self._deterministic_offset(key, len(pool))
        return dict(pool[idx])

    # ------------------------------------------------------------------
    # Reward selection
    # ------------------------------------------------------------------

    def select_rewards(
        self, min_level: int, count: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Select reward items appropriate for the level.

        Returns a list of item dicts with 'name', 'rarity', 'value'.
        """
        band = self._level_band(min_level)
        pool = _REWARD_POOLS.get(band, _REWARD_POOLS["low"])
        key = f"rewards:{min_level}"
        start = self._deterministic_offset(key, len(pool))
        result = []
        for i in range(count):
            item = pool[(start + i) % len(pool)]
            result.append(dict(item))
        return result

    def calculate_gold(self, min_level: int) -> int:
        """Calculate base gold reward for a given level."""
        return max(100, min_level * 25)

    # ------------------------------------------------------------------
    # Mission objectives
    # ------------------------------------------------------------------

    def get_mission_objectives(
        self, mission_type: str, min_level: int, area: str
    ) -> List[str]:
        """
        Generate mission objectives from templates.

        Returns a list of formatted objective strings.
        """
        templates = _MISSION_TEMPLATES.get(mission_type)
        if not templates:
            templates = _MISSION_TEMPLATES["exploration"]
        count = max(5, min_level // 10)
        return [t.format(area=area, count=count) for t in templates]

    # ------------------------------------------------------------------
    # Lever and Puzzle rooms
    # ------------------------------------------------------------------

    def get_lever_room(
        self, min_level: int, max_level: int
    ) -> Dict[str, Any]:
        """
        Generate a lever room configuration.

        Returns a dict with 'name', 'description', 'objectives'.
        """
        key = f"lever:{min_level}:{max_level}"
        idx = self._deterministic_offset(key, len(_LEVER_ROOM_TEMPLATES))
        return dict(_LEVER_ROOM_TEMPLATES[idx])

    def get_puzzle_room(
        self, min_level: int, max_level: int
    ) -> Dict[str, Any]:
        """
        Generate a puzzle room configuration.

        Returns a dict with 'name', 'description', 'objectives'.
        """
        key = f"puzzle:{min_level}:{max_level}"
        idx = self._deterministic_offset(key, len(_PUZZLE_ROOM_TEMPLATES))
        return dict(_PUZZLE_ROOM_TEMPLATES[idx])

    # ------------------------------------------------------------------
    # WorldModel integration helpers
    # ------------------------------------------------------------------

    def get_nearby_structures(
        self, x: int, y: int, z: int, radius: int = 50
    ) -> List[Structure]:
        """Find structures near a point using the WorldModel."""
        if self.world_model is None:
            return []
        return self.world_model.get_structures_in_area(
            x - radius, y - radius, x + radius, y + radius
        )

    def get_nearby_regions(
        self, x: int, y: int, z: int, radius: int = 100
    ) -> List[Region]:
        """Find regions near a point using the WorldModel."""
        if self.world_model is None:
            return []
        # Regions don't have coordinates in the current model,
        # so we return all regions as candidates
        return list(self.world_model.regions)