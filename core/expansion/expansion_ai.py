from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.world.world_model import WorldModel
from core.world.region import Region
from core.expansion.hunt_expander import HuntExpander, HuntExpansionResult
from core.expansion.boss_expander import BossExpander, BossExpansionResult
from core.expansion.region_expander import RegionExpander, RegionExpansionResult
from core.expansion.quest_zone_expander import QuestZoneExpander, QuestZoneExpansionResult
from core.expansion.road_expander import RoadExpander, RoadExpansionResult


@dataclass
class ExpansionResult:
    """Result of a single expansion step."""
    step_name: str = ""
    success: bool = False
    tiles_before: int = 0
    tiles_after: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_name": self.step_name,
            "success": self.success,
            "tiles_before": self.tiles_before,
            "tiles_after": self.tiles_after,
        }


@dataclass
class ExpansionReport:
    """Complete expansion report."""
    results: List[ExpansionResult] = field(default_factory=list)
    tiles_original: int = 0
    tiles_final: int = 0
    regions_original: int = 0
    regions_final: int = 0
    structures_original: int = 0
    structures_final: int = 0
    expanded: bool = False

    @property
    def tiles_added(self) -> int:
        return self.tiles_final - self.tiles_original

    def to_dict(self) -> Dict[str, Any]:
        return {
            "results": [r.to_dict() for r in self.results],
            "tiles_original": self.tiles_original,
            "tiles_final": self.tiles_final,
            "tiles_added": self.tiles_added,
            "regions_original": self.regions_original,
            "regions_final": self.regions_final,
            "structures_original": self.structures_original,
            "structures_final": self.structures_final,
            "expanded": self.expanded,
        }


class ExpansionAI:
    """
    Master orchestrator for content expansion.

    Detects empty zones, unused spaces, and incomplete regions,
    then generates new hunts, boss rooms, quest zones, mini dungeons,
    connections, and shortcuts.

    Integration:
      - OTBMImporter: Load world from file
      - MapAnalyzer: Detect empty/incomplete areas
      - BlueprintRegistry: Use blueprints for structures
      - EvolutionEngine: Post-expansion evolution

    Usage:
        ai = ExpansionAI()
        expanded, report = ai.expand(world)
        assert len(expanded.tiles) > len(original.tiles)
    """

    def __init__(self):
        self._hunt_expander = HuntExpander()
        self._boss_expander = BossExpander()
        self._region_expander = RegionExpander()
        self._quest_expander = QuestZoneExpander()
        self._road_expander = RoadExpander()

    def expand(self, world: WorldModel,
               max_hunts: int = 3,
               max_boss_rooms: int = 2,
               max_quest_zones: int = 3,
               boss_difficulty: str = "medium",
               theme: str = "cave") -> tuple:
        """
        Expand the world with new content.

        Args:
            world: WorldModel to expand in-place.
            max_hunts: Maximum hunt zones to create.
            max_boss_rooms: Maximum boss rooms to create.
            max_quest_zones: Maximum quest zones to create.
            boss_difficulty: Difficulty tier for boss rooms.
            theme: Theme for generated content.

        Returns:
            Tuple of (expanded WorldModel, ExpansionReport).
        """
        report = ExpansionReport()
        report.tiles_original = world.tile_count()
        report.regions_original = world.region_count()
        report.structures_original = world.structure_count()

        # Step 1: Fill gaps and connect existing regions
        self._run_step(report, "region_expansion", lambda:
            self._region_expander.expand(world, fill_gaps=True, connect_regions=True))

        # Step 2: Generate new hunt zones
        self._run_step(report, "hunt_expansion", lambda:
            self._hunt_expander.expand(world, max_hunts=max_hunts, theme=theme))

        # Step 3: Create boss rooms
        self._run_step(report, "boss_expansion", lambda:
            self._boss_expander.expand(world, max_rooms=max_boss_rooms,
                                       difficulty=boss_difficulty))

        # Step 4: Create quest zones
        self._run_step(report, "quest_zone_expansion", lambda:
            self._quest_expander.expand(world, max_zones=max_quest_zones))

        # Step 5: Build roads and shortcuts
        self._run_step(report, "road_expansion", lambda:
            self._road_expander.expand(world, create_shortcuts=True))

        # Final stats
        report.tiles_final = world.tile_count()
        report.regions_final = world.region_count()
        report.structures_final = world.structure_count()
        report.expanded = report.tiles_final > report.tiles_original

        return world, report

    def _run_step(self, report: ExpansionReport,
                  step_name: str, fn) -> None:
        """Execute an expansion step and record results."""
        result = ExpansionResult(step_name=step_name)
        try:
            step_result = fn()
            result.success = True
            if hasattr(step_result, "tiles_added"):
                result.tiles_after = result.tiles_before + step_result.tiles_added
        except Exception as e:
            result.success = False
        report.results.append(result)

    def analyze(self, world: WorldModel) -> Dict[str, Any]:
        """
        Analyze a world for expansion opportunities without modifying it.

        Returns:
            Dict with analysis results.
        """
        bounds = world._calculate_bounds()
        region_count = world.region_count()
        tile_count = world.tile_count()
        structure_count = world.structure_count()

        # Count spawns
        spawn_count = sum(
            1 for t in world.tiles.values() if t.spawn is not None
        )

        # Count zones with spawns vs without
        zones_with_spawns = set()
        zones_without_spawns = set()
        for t in world.tiles.values():
            if t.zone:
                if t.spawn:
                    zones_with_spawns.add(t.zone)
                else:
                    zones_without_spawns.add(t.zone)

        empty_zones = zones_without_spawns - zones_with_spawns

        return {
            "tile_count": tile_count,
            "region_count": region_count,
            "structure_count": structure_count,
            "spawn_count": spawn_count,
            "bounds": bounds,
            "zones_with_spawns": len(zones_with_spawns),
            "zones_without_spawns": len(empty_zones),
            "expansion_needed": tile_count < 500 or region_count < 3,
            "recommendations": self._generate_recommendations(
                tile_count, region_count, spawn_count, len(empty_zones)
            ),
        }

    def _generate_recommendations(self, tiles: int, regions: int,
                                  spawns: int, empty_zones: int) -> List[str]:
        """Generate expansion recommendations."""
        recs = []
        if tiles < 200:
            recs.append("World is very small; add hunt zones and quest areas")
        if regions < 2:
            recs.append("Add more regions for variety")
        if spawns < 10:
            recs.append("Add monster spawns for gameplay")
        if empty_zones > 0:
            recs.append(f"Fill {empty_zones} empty zone(s) with content")
        if regions >= 2 and spawns < regions * 5:
            recs.append("Regions lack sufficient spawns")
        return recs