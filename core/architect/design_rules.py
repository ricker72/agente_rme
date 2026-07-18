from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DesignRule:
    name: str
    description: str
    required: bool = True
    min_count: int = 1
    max_count: Optional[int] = None
    avoids: List[str] = field(default_factory=list)


@dataclass
class ZoneDesign:
    name: str
    zone_type: str
    purpose: str
    adjacent_to: List[str] = field(default_factory=list)
    avoid_near: List[str] = field(default_factory=list)
    min_distance_from_center: int = 0
    suggested_size: str = "medium"
    min_count: int = 1


@dataclass
class CompositionRules:
    flow_priority: float = 0.5
    risk_reward_balance: float = 0.5
    decoration_density: float = 0.5
    symmetry_factor: float = 0.3
    open_space_ratio: float = 0.4


class DesignRules:
    """
    Encodes architectural design rules for different Tibia map types.

    Responde: "¿Qué debería existir aquí?"

    City rules: Temple, Depot, Market, Residential, Roads.
    Dungeon rules: Entrance, Loop, Reward, Boss, Exit.
    Hunt rules: Flow, Risk, Reward, Density.
    """

    # ------------------------------------------------------------------
    # City Design Rules
    # ------------------------------------------------------------------

    CITY_MUST_HAVE = [
        DesignRule(
            "temple", "Central temple with respawn zone", required=True, min_count=1
        ),
        DesignRule(
            "depot", "Storage depot near central area", required=True, min_count=1
        ),
        DesignRule(
            "market",
            "Market plaza with stalls and fountain",
            required=True,
            min_count=1,
        ),
        DesignRule(
            "residential",
            "Housing district with walls",
            required=True,
            min_count=2,
            max_count=8,
        ),
        DesignRule(
            "roads",
            "Connected road network between districts",
            required=True,
            min_count=3,
        ),
        DesignRule("gate", "Entry/exit gate to the city", required=False, min_count=1),
        DesignRule("training", "Training area / arena", required=False),
        DesignRule("ship", "Ship/boat dock for travel", required=False),
    ]

    CITY_SHOULD_AVOID = [
        "square repetitive rooms",
        "endless corridors",
        "empty open spaces without decoration",
        "excessive symmetry (mirror layout)",
        "isolated districts with no road connection",
    ]

    CITY_ZONES = [
        ZoneDesign(
            "Temple District",
            "Temple",
            "Safe respawn and blessing area",
            adjacent_to=["Market", "Residential"],
            avoid_near=["Harbor"],
        ),
        ZoneDesign(
            "Depot Quarter",
            "Depot",
            "Item storage and banking",
            adjacent_to=["Market", "Residential"],
        ),
        ZoneDesign(
            "Central Plaza",
            "Market",
            "Commerce, NPCs, fountain",
            adjacent_to=["Temple District", "Depot Quarter", "Residential"],
            suggested_size="large",
        ),
        ZoneDesign(
            "Residential Block",
            "Residential",
            "Player housing",
            adjacent_to=["Central Plaza", "Depot Quarter"],
            min_count=2,
        ),
        ZoneDesign(
            "Harbor Front",
            "Harbor",
            "Docks and ship travel",
            adjacent_to=["Market"],
            avoid_near=["Temple District"],
        ),
    ]

    # ------------------------------------------------------------------
    # Dungeon Design Rules
    # ------------------------------------------------------------------

    DUNGEON_MUST_HAVE = [
        DesignRule(
            "entrance", "Entry point to the dungeon", required=True, min_count=1
        ),
        DesignRule(
            "loop",
            "Circular path allowing return without backtracking",
            required=True,
            min_count=1,
        ),
        DesignRule(
            "reward", "Treasure room or special loot area", required=True, min_count=1
        ),
        DesignRule(
            "boss", "Boss room with special mechanics", required=True, min_count=1
        ),
        DesignRule(
            "exit", "Exit point (may be same as entrance)", required=True, min_count=1
        ),
        DesignRule("quest", "Quest room with unique content", required=False),
        DesignRule(
            "shortcut",
            "Teleport or passage bypassing sections",
            required=False,
            min_count=0,
            max_count=4,
        ),
    ]

    DUNGEON_SHOULD_AVOID = [
        "dead-end rooms with no purpose",
        "single corridor without branching",
        "all rooms same size",
        "boss accessible without any exploration",
        "treasure rooms adjacent to entrance",
    ]

    DUNGEON_ZONES = [
        ZoneDesign(
            "Grand Hall",
            "CombatRoom",
            "First combat encounter",
            adjacent_to=["Entrance"],
            suggested_size="large",
        ),
        ZoneDesign(
            "Dark Passage",
            "Corridor",
            "Connecting corridor with ambush",
            adjacent_to=["Grand Hall", "Vault"],
        ),
        ZoneDesign(
            "Crystal Vault",
            "TreasureRoom",
            "Loot and rare items",
            adjacent_to=["Dark Passage"],
            avoid_near=["Entrance"],
            min_distance_from_center=3,
        ),
        ZoneDesign(
            "Ancient Sanctum",
            "BossRoom",
            "Final boss encounter",
            adjacent_to=["Dark Passage"],
            avoid_near=["Entrance", "Crystal Vault"],
            suggested_size="large",
        ),
        ZoneDesign(
            "Sealed Chamber",
            "QuestRoom",
            "Optional quest content",
            adjacent_to=["Dark Passage"],
        ),
        ZoneDesign(
            "Collapsed Tunnel",
            "Shortcut",
            "Quick return path",
            adjacent_to=["Ancient Sanctum", "Grand Hall"],
        ),
    ]

    # ------------------------------------------------------------------
    # Hunt Zone Design Rules
    # ------------------------------------------------------------------

    HUNT_MUST_HAVE = [
        DesignRule("flow", "Smooth progression path through the hunt", required=True),
        DesignRule("risk", "Danger zones with harder monsters", required=True),
        DesignRule("reward", "Loot areas with valuable drops", required=True),
        DesignRule(
            "density", "Appropriate monster density for the level", required=True
        ),
        DesignRule(
            "safe_spots", "Safe spots for regrouping", required=False, min_count=2
        ),
        DesignRule("variety", "Mixed monster types (not all same)", required=True),
    ]

    HUNT_SHOULD_AVOID = [
        "all monsters in one room",
        "no escape routes from danger zones",
        "flat reward curve (all same risk)",
        "excessive backtracking",
        "decorative items that block movement",
    ]

    HUNT_ZONES = [
        ZoneDesign("Entry Chamber", "Spawn", "warmup", suggested_size="medium"),
        ZoneDesign("Hunting Grounds", "Spawn", "grinding", suggested_size="large"),
        ZoneDesign("Elite Chamber", "Spawn", "risk", suggested_size="medium"),
        ZoneDesign("Treasure Vault", "Reward", "reward", avoid_near=["Entry Chamber"]),
        ZoneDesign(
            "Boss Arena",
            "Boss",
            "boss",
            avoid_near=["Entry Chamber", "Treasure Vault"],
            suggested_size="large",
        ),
        ZoneDesign("Safe Corridor", "SafeZone", "safety", min_count=2),
    ]

    # ------------------------------------------------------------------
    # Rule application
    # ------------------------------------------------------------------

    @classmethod
    def for_city(cls) -> List[DesignRule]:
        return cls.CITY_MUST_HAVE

    @classmethod
    def for_dungeon(cls) -> List[DesignRule]:
        return cls.DUNGEON_MUST_HAVE

    @classmethod
    def for_hunt(cls) -> List[DesignRule]:
        return cls.HUNT_MUST_HAVE

    @classmethod
    def zones_for(cls, map_type: str) -> List[ZoneDesign]:
        mapping = {
            "city": cls.CITY_ZONES,
            "dungeon": cls.DUNGEON_ZONES,
            "hunt": cls.HUNT_ZONES,
        }
        return mapping.get(map_type, [])

    @classmethod
    def violations_for(cls, map_type: str, zones_present: List[str]) -> List[str]:
        """Check which required rules are violated by the current zones."""
        required = (
            cls.for_city()
            if map_type == "city"
            else (cls.for_dungeon() if map_type == "dungeon" else cls.for_hunt())
        )
        violations = []
        for rule in required:
            if rule.required and rule.name not in zones_present:
                violations.append(
                    f"Missing required element: {rule.name} ({rule.description})"
                )
        return violations

    @classmethod
    def avoid_list(cls, map_type: str) -> List[str]:
        mapping = {
            "city": cls.CITY_SHOULD_AVOID,
            "dungeon": cls.DUNGEON_SHOULD_AVOID,
            "hunt": cls.HUNT_SHOULD_AVOID,
        }
        return mapping.get(map_type, [])
