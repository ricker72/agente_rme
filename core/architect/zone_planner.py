"""
HITO 15 — AI Architect: Zone Planner
====================================

Plans individual zones for the world: City, Dungeon, Hunt, Boss, and Quest.

Each zone is a self-contained building block that knows:
    - What type it is (city / dungeon / hunt / boss / quest)
    - What structures it must contain (e.g. a city has temple+depot+market+houses)
    - Its bounds (x, y, w, h) inside the world
    - Its difficulty and monster pool
    - Which theme assets it uses

The ZonePlanner does NOT decide positions: that is the LayoutPlanner's job.
It only decides WHAT each zone should contain and its intrinsic properties.

Architecture:
    ThemeAssets + DifficultyProfile + request
        ↓
    ZonePlanner.plan_city(...) / plan_dungeon(...) / ...
        ↓
    CityPlan / DungeonPlan / HuntPlan / BossPlan / QuestPlan
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .theme_resolver import ThemeAssets


# =============================================================================
# Difficulty band definitions
# =============================================================================

DIFFICULTY_BANDS: List[Dict[str, Any]] = [
    {"label": "easy",       "min": 1,   "max": 50,   "rank": 1},
    {"label": "medium",     "min": 50,  "max": 100,  "rank": 2},
    {"label": "hard",       "min": 100, "max": 200,  "rank": 3},
    {"label": "extreme",    "min": 200, "max": 300,  "rank": 4},
    {"label": "epic",       "min": 300, "max": 500,  "rank": 5},
    {"label": "legendary",  "min": 500, "max": 9999, "rank": 6},
]


# =============================================================================
# Zone-specific plan dataclasses
# =============================================================================

@dataclass
class CityPlan:
    """A complete city plan: districts + features + population."""
    name: str
    theme: str
    population: int
    districts: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    min_level: int = 1
    max_level: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "theme": self.theme,
            "population": self.population,
            "districts": self.districts,
            "features": self.features,
            "level_range": [self.min_level, self.max_level],
            "metadata": self.metadata,
        }


@dataclass
class DungeonPlan:
    """A complete dungeon plan: floors + rooms + loot tiers + boss."""
    name: str
    theme: str
    floors: int
    difficulty: str
    room_count: int
    rooms: List[Dict[str, Any]] = field(default_factory=list)
    boss: Optional[Dict[str, Any]] = None
    min_level: int = 1
    max_level: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "theme": self.theme,
            "floors": self.floors,
            "difficulty": self.difficulty,
            "room_count": self.room_count,
            "rooms": self.rooms,
            "boss": self.boss,
            "level_range": [self.min_level, self.max_level],
            "metadata": self.metadata,
        }


@dataclass
class HuntPlan:
    """A complete hunt plan: monster pool, density, area size, geometry."""
    name: str
    theme: str
    min_level: int
    max_level: int
    monster_pool: List[str] = field(default_factory=list)
    spawn_density: str = "medium"
    area_size: Tuple[int, int] = (50, 50)
    spawn_count: int = 10
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "theme": self.theme,
            "level_range": [self.min_level, self.max_level],
            "monster_pool": self.monster_pool,
            "spawn_density": self.spawn_density,
            "area_size": list(self.area_size),
            "spawn_count": self.spawn_count,
            "metadata": self.metadata,
        }


@dataclass
class BossPlan:
    """A complete boss plan: monster, arena, mechanics, loot."""
    name: str
    theme: str
    boss_monster: str
    arena_size: Tuple[int, int]
    min_level: int
    max_level: int
    mechanics: List[str] = field(default_factory=list)
    loot_table: List[str] = field(default_factory=list)
    minions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "theme": self.theme,
            "boss_monster": self.boss_monster,
            "arena_size": list(self.arena_size),
            "level_range": [self.min_level, self.max_level],
            "mechanics": self.mechanics,
            "loot_table": self.loot_table,
            "minions": self.minions,
            "metadata": self.metadata,
        }


@dataclass
class QuestPlan:
    """A complete quest plan: title, objectives, NPCs, rewards."""
    name: str
    title: str
    theme: str
    min_level: int
    max_level: int
    objectives: List[Dict[str, Any]] = field(default_factory=list)
    npcs: List[str] = field(default_factory=list)
    rewards: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "theme": self.theme,
            "level_range": [self.min_level, self.max_level],
            "objectives": self.objectives,
            "npcs": self.npcs,
            "rewards": self.rewards,
            "metadata": self.metadata,
        }


# =============================================================================
# Zone Planner
# =============================================================================

class ZonePlanner:
    """
    Builds detailed plans for each kind of zone (city, dungeon, hunt, boss, quest).

    The planner uses:
        - a ThemeAssets (knows what materials/creatures to use)
        - a level range (drives difficulty band)
        - a request (describes what the prompt asked for)

    All public plan_* methods return a populated plan dataclass that can be
    fed directly to the LayoutPlanner for placement, or to the
    WorldGenerator for execution.

    Usage:
        planner = ZonePlanner()
        theme = resolve_theme("issavi")
        city = planner.plan_city("Issavi Capital", theme, min_level=200, max_level=500)
    """

    # City district templates by theme difficulty
    CITY_DISTRICTS_BY_BAND: Dict[str, List[str]] = {
        "easy":       ["Market", "Temple", "Houses", "Town Square"],
        "medium":     ["Market", "Temple", "Depot", "Houses", "Tavern"],
        "hard":       ["Temple District", "Depot Quarter", "Central Plaza",
                       "Residential Block", "Market", "Harbor Front"],
        "extreme":    ["Temple District", "Depot Quarter", "Central Plaza",
                       "Residential Block A", "Residential Block B", "Market",
                       "Harbor Front", "Arena"],
        "epic":       ["Temple District", "Depot Quarter", "Central Plaza",
                       "Residential Block A", "Residential Block B",
                       "Market", "Harbor Front", "Arena", "Noble Quarter"],
        "legendary":  ["Temple District", "Depot Quarter", "Grand Plaza",
                       "Residential Block A", "Residential Block B",
                       "Residential Block C", "Market", "Harbor Front",
                       "Arena", "Noble Quarter", "Wizard Tower"],
    }

    # Default room distribution per dungeon floor
    DUNGEON_ROOMS_PER_FLOOR: Dict[str, int] = {
        "easy": 3, "medium": 5, "hard": 7, "extreme": 9,
        "epic": 11, "legendary": 14,
    }

    # Boss mechanics per difficulty
    BOSS_MECHANICS: Dict[str, List[str]] = {
        "easy":       ["melee", "single_target"],
        "medium":     ["melee", "aoe_burst", "summon_minions"],
        "hard":       ["melee", "aoe_burst", "summon_minions", "ranged"],
        "extreme":    ["melee", "aoe_burst", "summon_minions", "ranged",
                       "status_inflight", "teleport", "heal"],
        "epic":       ["melee", "aoe_burst", "summon_minions", "ranged",
                       "status_inflight", "teleport", "heal", "lifesteal",
                       "shields", "waves"],
        "legendary":  ["melee", "aoe_burst", "summon_minions", "ranged",
                       "status_inflight", "teleport", "heal", "lifesteal",
                       "shields", "waves", "phases", "enrage"],
    }

    # Quest objective templates
    QUEST_OBJECTIVES: List[str] = [
        "Slay {count} {monster} in {location}",
        "Recover the {item} from {location}",
        "Speak with {npc} at {location}",
        "Defeat the {boss} at {location}",
        "Explore {count} rooms of {location}",
        "Escort the {npc} through {location}",
    ]

    # Quest NPC names
    QUEST_NPCS: List[str] = [
        "Old Hermit", "Ship Captain", "Royal Advisor", "Tavern Keeper",
        "Wandering Monk", "Mysterious Stranger", "Retired Hunter",
        "Royal Mage", "Village Elder", "Dwarven Engineer",
    ]

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    # ------------------------------------------------------------------
    # Difficulty classification
    # ------------------------------------------------------------------

    def classify_difficulty(self, level: int) -> str:
        """Classify a single level into a difficulty band."""
        return self.classify_range(level, level)

    def classify_range(self, min_level: int, max_level: int) -> str:
        """Classify a level range into a difficulty band (uses the midpoint)."""
        mid = (min_level + max_level) // 2
        for band in DIFFICULTY_BANDS:
            if band["min"] <= mid <= band["max"]:
                return band["label"]
        # Out-of-range fallbacks
        if mid < DIFFICULTY_BANDS[0]["min"]:
            return DIFFICULTY_BANDS[0]["label"]
        return DIFFICULTY_BANDS[-1]["label"]

    def difficulty_rank(self, label: str) -> int:
        """Get the numeric rank for a difficulty label (1=easy ... 6=legendary)."""
        for band in DIFFICULTY_BANDS:
            if band["label"] == label:
                return band["rank"]
        return 2  # default to medium

    # ------------------------------------------------------------------
    # City planning
    # ------------------------------------------------------------------

    def plan_city(
        self,
        name: str,
        theme: ThemeAssets,
        min_level: int = 1,
        max_level: int = 100,
        population: Optional[int] = None,
        seed: Optional[int] = None,
    ) -> CityPlan:
        """
        Build a detailed city plan.

        The number of districts, features, and population scale with the
        difficulty band derived from the level range.
        """
        rng = random.Random(seed) if seed is not None else self._rng
        band = self.classify_range(min_level, max_level)
        districts = list(self.CITY_DISTRICTS_BY_BAND.get(band, []))

        # Theme-specific district flavor
        biome = theme.metadata.get("biome", "")
        if "desert" in biome:
            districts.append("Oasis Quarter")
        if "nightmare" in biome:
            districts.append("Twilight Court")
        if "arcane" in biome:
            districts.append("Wizard Tower")
        if "exotic" in biome:
            districts.append("Merchant Court")

        # Population scales with level (denser cities for higher levels)
        if population is None:
            base = 200
            scale = max(1, (max_level - min_level) // 10)
            population = base + scale * 150 + len(districts) * 80

        # Features that any city of this band should have
        features = ["roads", "lighting"]
        if self.difficulty_rank(band) >= 2:
            features.append("temple")
        if self.difficulty_rank(band) >= 3:
            features.append("depot")
            features.append("market_stalls")
        if self.difficulty_rank(band) >= 4:
            features.append("arena")
            features.append("ship_dock")
        if self.difficulty_rank(band) >= 5:
            features.append("noble_quarter")
            features.append("training_ground")

        return CityPlan(
            name=name,
            theme=theme.name,
            population=population,
            districts=districts,
            features=features,
            min_level=min_level,
            max_level=max_level,
            metadata={
                "band": band,
                "biome": theme.metadata.get("biome", "generic"),
                "era": theme.metadata.get("era", "modern"),
                "grounds": theme.grounds[:3],
                "walls": theme.walls[:3],
            },
        )

    # ------------------------------------------------------------------
    # Dungeon planning
    # ------------------------------------------------------------------

    def plan_dungeon(
        self,
        name: str,
        theme: ThemeAssets,
        min_level: int = 1,
        max_level: int = 200,
        floors: int = 0,
        include_boss: bool = True,
        boss_monster: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> DungeonPlan:
        """
        Build a detailed dungeon plan with floors, rooms, and boss.

        Number of rooms per floor scales with difficulty; boss is the
        strongest monster in the theme's pool by default.
        """
        rng = random.Random(seed) if seed is not None else self._rng
        band = self.classify_range(min_level, max_level)
        rank = self.difficulty_rank(band)

        # Default floor count by difficulty
        if floors <= 0:
            floors = max(1, rank)

        # Rooms per floor
        rooms_per_floor = self.DUNGEON_ROOMS_PER_FLOOR.get(band, 7)
        total_rooms = rooms_per_floor * floors

        # Build room list (just metadata, no positions here)
        rooms: List[Dict[str, Any]] = []
        for i in range(total_rooms):
            room_type = rng.choice(
                ["combat", "treasure", "lore", "trap", "ambush", "shrine"]
            )
            room_level = min_level + (i % floors) * ((max_level - min_level) // max(1, floors))
            rooms.append({
                "id": f"room_{i:03d}",
                "type": room_type,
                "floor": i % floors,
                "level": room_level,
                "monster_count": rng.randint(2, 6),
            })

        # Boss room
        boss: Optional[Dict[str, Any]] = None
        if include_boss and theme.monsters:
            boss_name = boss_monster or theme.monsters[0]
            boss = {
                "name": boss_name,
                "level": max_level,
                "room_id": f"room_{(floors * rooms_per_floor) - 1:03d}",
                "mechanics": self.BOSS_MECHANICS.get(band, ["melee"]),
            }

        return DungeonPlan(
            name=name,
            theme=theme.name,
            floors=floors,
            difficulty=band,
            room_count=total_rooms,
            rooms=rooms,
            boss=boss,
            min_level=min_level,
            max_level=max_level,
            metadata={
                "rooms_per_floor": rooms_per_floor,
                "biome": theme.metadata.get("biome", "generic"),
                "has_boss": include_boss,
                "grounds": theme.grounds[:3],
                "walls": theme.walls[:3],
            },
        )

    # ------------------------------------------------------------------
    # Hunt planning
    # ------------------------------------------------------------------

    def plan_hunt(
        self,
        name: str,
        theme: ThemeAssets,
        min_level: int = 1,
        max_level: int = 200,
        area_size: Tuple[int, int] = (50, 50),
        density: str = "medium",
        seed: Optional[int] = None,
    ) -> HuntPlan:
        """
        Build a detailed hunt plan with monster pool, density, and area.

        Monster pool is taken from the theme's monster list; spawn count
        scales with area and density.
        """
        rng = random.Random(seed) if seed is not None else self._rng
        band = self.classify_range(min_level, max_level)

        # Pick a balanced subset of monsters from the theme
        pool = list(theme.monsters) if theme.monsters else ["Demon"]
        if not pool:
            pool = ["Demon"]

        # Spawn count scales with area and density
        area = area_size[0] * area_size[1]
        density_mult = {"low": 0.4, "medium": 1.0, "high": 1.8, "extreme": 2.5}.get(
            density, 1.0
        )
        spawn_count = max(5, int(area / 200 * density_mult * 10))

        return HuntPlan(
            name=name,
            theme=theme.name,
            min_level=min_level,
            max_level=max_level,
            monster_pool=pool,
            spawn_density=density,
            area_size=area_size,
            spawn_count=spawn_count,
            metadata={
                "band": band,
                "biome": theme.metadata.get("biome", "generic"),
                "grounds": theme.grounds[:3],
                "walls": theme.walls[:3],
                "decorations": theme.decorations[:3],
            },
        )

    # ------------------------------------------------------------------
    # Boss planning
    # ------------------------------------------------------------------

    def plan_boss(
        self,
        name: str,
        theme: ThemeAssets,
        min_level: int = 200,
        max_level: int = 500,
        boss_monster: Optional[str] = None,
        arena_size: Tuple[int, int] = (16, 16),
        seed: Optional[int] = None,
    ) -> BossPlan:
        """
        Build a detailed boss plan with mechanics, loot, and minions.
        """
        rng = random.Random(seed) if seed is not None else self._rng
        band = self.classify_range(min_level, max_level)

        # Default boss is the strongest monster in the pool
        boss_name = boss_monster or (theme.monsters[0] if theme.monsters else "Demon")

        # Minions are the rest of the pool
        minions = [m for m in theme.monsters if m != boss_name] if theme.monsters else []

        # Loot scales with band
        loot_table = self._boss_loot(band, rng)

        # Mechanics scale with band
        mechanics = self.BOSS_MECHANICS.get(band, ["melee"])

        return BossPlan(
            name=name,
            theme=theme.name,
            boss_monster=boss_name,
            arena_size=arena_size,
            min_level=min_level,
            max_level=max_level,
            mechanics=mechanics,
            loot_table=loot_table,
            minions=minions[:3],
            metadata={
                "band": band,
                "biome": theme.metadata.get("biome", "generic"),
                "arena_theme_grounds": theme.grounds[:2],
                "arena_theme_walls": theme.walls[:2],
            },
        )

    # ------------------------------------------------------------------
    # Quest planning
    # ------------------------------------------------------------------

    def plan_quest(
        self,
        title: str,
        theme: ThemeAssets,
        min_level: int = 1,
        max_level: int = 200,
        objective_count: int = 3,
        seed: Optional[int] = None,
    ) -> QuestPlan:
        """
        Build a detailed quest plan with objectives, NPCs, and rewards.
        """
        rng = random.Random(seed) if seed is not None else self._rng
        band = self.classify_range(min_level, max_level)

        # Build a location label from the theme
        location = self._quest_location(theme)

        # Pick a quest-giving NPC
        npc = rng.choice(self.QUEST_NPCS)

        # Build objectives
        objectives: List[Dict[str, Any]] = []
        used_templates: List[str] = []
        for i in range(objective_count):
            template = rng.choice(
                [t for t in self.QUEST_OBJECTIVES if t not in used_templates]
            )
            used_templates.append(template)
            objective = {
                "id": f"obj_{i:02d}",
                "description": template.format(
                    count=rng.randint(3, 12),
                    monster=theme.pick_monster(i),
                    location=location,
                    item=rng.choice(["Sacred Relic", "Ancient Map", "Crystal Shard",
                                     "Tome of Power", "Royal Signet", "Mystic Orb"]),
                    npc=npc,
                    boss=theme.pick_monster(0),
                ),
                "type": template.split("{")[0].strip().lower(),
                "level": min_level + i * ((max_level - min_level) // max(1, objective_count)),
            }
            objectives.append(objective)

        # Build rewards (band-aware)
        rewards = self._quest_rewards(band, rng)

        return QuestPlan(
            name=title.lower().replace(" ", "_").replace("'", ""),
            title=title,
            theme=theme.name,
            min_level=min_level,
            max_level=max_level,
            objectives=objectives,
            npcs=[npc],
            rewards=rewards,
            metadata={
                "band": band,
                "biome": theme.metadata.get("biome", "generic"),
                "location": location,
            },
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _boss_loot(self, band: str, rng: random.Random) -> List[str]:
        loot_by_band: Dict[str, List[str]] = {
            "easy":      ["Gold Coin", "Health Potion", "Bread"],
            "medium":    ["Platinum Coin", "Ultimate Health Potion", "Crystal Sword",
                          "Royal Helmet"],
            "hard":      ["Gold Ingot", "Supreme Health Potion", "Mastermind Shield",
                          "Dragon Scale Boots", "Frazzlemaw Tongue"],
            "extreme":   ["Demonic Essence", "Great Mana Potion", "Spellbook of Wards",
                          "Vampire Lord Token", "Cloak of Terror"],
            "epic":      ["Soul War Relic", "Frozen Heart", "Soulshard",
                          "Hellstalker Edge", "Dream Warden Boots"],
            "legendary": ["Legendary Token", "Master Shroud", "Soulcutter",
                          "Riftwalker Cape", "Hellforged Helm"],
        }
        base = loot_by_band.get(band, loot_by_band["medium"])
        count = {"easy": 2, "medium": 3, "hard": 3, "extreme": 4, "epic": 4, "legendary": 5}.get(
            band, 3
        )
        return rng.sample(base, min(count, len(base)))

    def _quest_rewards(self, band: str, rng: random.Random) -> List[str]:
        reward_by_band: Dict[str, List[str]] = {
            "easy":      ["1000 Gold", "Experience (5000)"],
            "medium":    ["5000 Gold", "Experience (25000)", "Minor Loot Box"],
            "hard":      ["15000 Gold", "Experience (75000)", "Skill Boost",
                          "Temple Blessing"],
            "extreme":   ["50000 Gold", "Experience (200000)", "Achievement Point",
                          "Access to Hunt Zone", "Rare Mount"],
            "epic":      ["100000 Gold", "Experience (500000)", "Legendary Outfit",
                          "Outfit Unlock", "Title: Hero of {theme}"],
            "legendary": ["500000 Gold", "Experience (1500000)", "Custom Outfit",
                          "Announcement Reward", "Unique Weapon Skin"],
        }
        base = reward_by_band.get(band, reward_by_band["medium"])
        count = {"easy": 1, "medium": 2, "hard": 2, "extreme": 3, "epic": 3, "legendary": 4}.get(
            band, 2
        )
        return rng.sample(base, min(count, len(base)))

    def _quest_location(self, theme: ThemeAssets) -> str:
        biome = theme.metadata.get("biome", "")
        base = theme.name.capitalize()
        if "desert" in biome:
            return f"{base} Sand Temple"
        if "nightmare" in biome:
            return f"{base} Nightmare Court"
        if "arcane" in biome:
            return f"{base} Arcane Library"
        if "exotic" in biome:
            return f"{base} Plaza"
        if "nether" in biome:
            return f"{base} Soul Altar"
        return f"{base} Depths"


# =============================================================================
# Module-level convenience
# =============================================================================

_DEFAULT_PLANNER: Optional[ZonePlanner] = None


def get_default_planner() -> ZonePlanner:
    """Return a process-wide default planner (lazy initialization)."""
    global _DEFAULT_PLANNER
    if _DEFAULT_PLANNER is None:
        _DEFAULT_PLANNER = ZonePlanner()
    return _DEFAULT_PLANNER
