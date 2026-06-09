"""
Route Simulator — Evaluates hunting route efficiency.

Measures XP/H, Profit/H, and Travel Time for a given route
through a set of spawn zones. Used to detect broken hunts
before exporting map blueprints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class RouteMetrics:
    """Aggregated metrics for a hunting route."""
    total_xp: int = 0
    total_profit: int = 0
    travel_time_seconds: float = 0.0       # time spent walking between spawns
    combat_time_seconds: float = 0.0       # time spent in combat
    total_time_seconds: float = 0.0        # sum of travel + combat
    monsters_killed: int = 0
    deaths: int = 0

    @property
    def xp_per_hour(self) -> float:
        if self.total_time_seconds <= 0:
            return 0.0
        return (self.total_xp / self.total_time_seconds) * 3600.0

    @property
    def profit_per_hour(self) -> float:
        if self.total_time_seconds <= 0:
            return 0.0
        return (self.total_profit / self.total_time_seconds) * 3600.0

    @property
    def travel_time_minutes(self) -> float:
        return self.travel_time_seconds / 60.0

    @property
    def combat_time_minutes(self) -> float:
        return self.combat_time_seconds / 60.0

    @property
    def total_time_minutes(self) -> float:
        return self.total_time_seconds / 60.0

    def to_dict(self) -> Dict:
        return {
            "total_xp": self.total_xp,
            "total_profit": self.total_profit,
            "xp_per_hour": round(self.xp_per_hour, 1),
            "profit_per_hour": round(self.profit_per_hour, 1),
            "travel_time_min": round(self.travel_time_minutes, 2),
            "combat_time_min": round(self.combat_time_minutes, 2),
            "total_time_min": round(self.total_time_minutes, 2),
            "monsters_killed": self.monsters_killed,
            "deaths": self.deaths,
        }


@dataclass
class RouteResult:
    """Complete result of a route simulation."""
    route_name: str
    metrics: RouteMetrics = field(default_factory=RouteMetrics)
    viable: bool = True
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "route_name": self.route_name,
            "metrics": self.metrics.to_dict(),
            "viable": self.viable,
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# Waypoint / spawn zone
# ---------------------------------------------------------------------------

@dataclass
class SpawnZone:
    """
    A spawn area within a hunting route.

    Contains a group of monsters that respawn and can be fought.
    """
    name: str
    monster_name: str
    monster_count: int          # how many monsters are in this zone
    monster_xp_each: int        # XP per monster kill
    monster_damage_each: int    # average damage per monster per turn
    monster_hp_each: int        # HP per monster
    respawn_seconds: float = 30.0  # respawn delay
    travel_from_previous_seconds: float = 10.0  # walk time from last zone


# ---------------------------------------------------------------------------
# Route Simulator
# ---------------------------------------------------------------------------

class RouteSimulator:
    """
    Simulates running a hunting route composed of spawn zones.

    A route is a sequence of SpawnZone objects that a player/party
    visits in order. The simulator tracks travel time, combat duration,
    kills, XP, profit, and death count.
    """

    def __init__(self, route_name: str = "unnamed"):
        self.route_name = route_name
        self.zones: List[SpawnZone] = []

    def add_zone(self, zone: SpawnZone) -> None:
        self.zones.append(zone)

    def run(
        self,
        player_dps: float,
        max_combat_duration: float = 300.0,   # max seconds before stopping combat
        cycles: int = 1,                       # how many times to loop the route
        loot_gp_per_kill: int = 0,             # average gp loot per kill
    ) -> RouteResult:
        """
        Run the route simulation.

        Parameters
        ----------
        player_dps : float
            Total damage per second the player/party can output.
        max_combat_duration : float
            Maximum seconds to spend fighting in a single zone before moving on.
        cycles : int
            Number of times to loop the entire route sequence.
        loot_gp_per_kill : int
            Average gold value of loot dropped per monster.

        Returns
        -------
        RouteResult with metrics, viability, and any warnings.
        """
        metrics = RouteMetrics()
        warnings: List[str] = []

        for cycle in range(cycles):
            for zone in self.zones:
                # -- Travel time --
                metrics.travel_time_seconds += zone.travel_from_previous_seconds

                # -- Combat phase --
                # Time to kill one monster
                ttk = zone.monster_hp_each / max(1.0, player_dps)

                # Monsters killed before respawn or max duration
                monsters_alive = zone.monster_count
                combat_time = 0.0
                kills_this_zone = 0

                while monsters_alive > 0 and combat_time < max_combat_duration:
                    # How many monsters can we kill in the remaining time?
                    killable = int((max_combat_duration - combat_time) / max(0.01, ttk))
                    killable = min(killable, monsters_alive)

                    if killable <= 0:
                        break

                    kills_this_zone += killable
                    monsters_alive -= killable
                    combat_time += killable * ttk

                    # Incoming damage while fighting
                    avg_alive = (monsters_alive + killable / 2)
                    total_incoming_damage = avg_alive * zone.monster_damage_each * ttk * killable

                    # Check for deaths: if incoming damage per second > effective HP buffer
                    # Simplified death check: if a zone does enough damage to kill in < 5s
                    effective_health = 1500.0  # default assumption; overridden by combat sim
                    if total_incoming_damage > effective_health * 2:
                        deaths = int(total_incoming_damage / effective_health) - 1
                        metrics.deaths += max(0, deaths)

                    # If respawn happened during combat, refill some
                    if combat_time >= zone.respawn_seconds and monsters_alive == 0:
                        monsters_alive = zone.monster_count
                        zone.respawn_seconds += zone.respawn_seconds  # next respawn later

                metrics.combat_time_seconds += combat_time
                metrics.monsters_killed += kills_this_zone
                metrics.total_xp += kills_this_zone * zone.monster_xp_each

                # Profit from loot
                metrics.total_profit += kills_this_zone * loot_gp_per_kill

                # Warnings
                if combat_time >= max_combat_duration and kills_this_zone < zone.monster_count * 0.5:
                    warnings.append(
                        f"Zone '{zone.name}' too difficult: only {kills_this_zone}/{zone.monster_count} "
                        f"killed before time cap ({max_combat_duration}s)"
                    )

        metrics.total_time_seconds = metrics.travel_time_seconds + metrics.combat_time_seconds

        # Viability assessment
        viable = True
        if metrics.xp_per_hour < 100000:
            warnings.append(f"Low XP/H: {metrics.xp_per_hour:.0f} (threshold: 100k)")
            viable = False
        if metrics.profit_per_hour < -50000:
            warnings.append(f"Negative profit/H: {metrics.profit_per_hour:.0f} gp/h")
            viable = False
        if metrics.deaths > 0:
            warnings.append(f"Route caused {metrics.deaths} death(s) — too dangerous")
            viable = False
        if metrics.travel_time_seconds > metrics.combat_time_seconds * 0.5:
            warnings.append(
                f"Excessive travel time: {metrics.travel_time_minutes:.1f}min travel vs "
                f"{metrics.combat_time_minutes:.1f}min combat"
            )
            viable = False

        return RouteResult(
            route_name=self.route_name,
            metrics=metrics,
            viable=viable,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_zone_dicts(
        cls,
        route_name: str,
        zones: List[Dict],
    ) -> RouteSimulator:
        """
        Build a route from a list of zone dictionaries.

        Each dict must have keys: name, monster_name, monster_count,
        monster_xp_each, monster_damage_each, monster_hp_each.
        Optional: respawn_seconds, travel_from_previous_seconds.
        """
        sim = cls(route_name)
        for z in zones:
            sim.add_zone(SpawnZone(
                name=z["name"],
                monster_name=z["monster_name"],
                monster_count=z.get("monster_count", 5),
                monster_xp_each=z.get("monster_xp_each", 1000),
                monster_damage_each=z.get("monster_damage_each", 100),
                monster_hp_each=z.get("monster_hp_each", 2000),
                respawn_seconds=float(z.get("respawn_seconds", 30)),
                travel_from_previous_seconds=float(z.get("travel_from_previous_seconds", 10)),
            ))
        return sim

    @classmethod
    def quick_route(
        cls,
        name: str,
        monster_name: str,
        count: int = 5,
        xp: int = 1000,
        damage: int = 100,
        hp: int = 2000,
        travel: float = 0,
    ) -> RouteSimulator:
        """Create a single-zone route for quick testing."""
        sim = cls(name)
        sim.add_zone(SpawnZone(
            name=name,
            monster_name=monster_name,
            monster_count=count,
            monster_xp_each=xp,
            monster_damage_each=damage,
            monster_hp_each=hp,
            travel_from_previous_seconds=travel,
        ))
        return sim