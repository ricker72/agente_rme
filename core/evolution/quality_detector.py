from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ZoneCategory(Enum):
    CITY = "city"
    HUNT = "hunt"
    BOSS_ROOM = "boss_room"
    QUEST_ZONE = "quest_zone"
    CAVE = "cave"
    WILDERNESS = "wilderness"
    TRANSITION = "transition"
    EMPTY = "empty"


@dataclass
class ZoneMetrics:
    tile_count: int = 0
    walkable_tiles: int = 0
    blocked_tiles: int = 0
    ground_variety: int = 0
    decoration_count: int = 0
    spawn_count: int = 0
    monster_types: int = 0
    navigation_nodes: int = 0
    dead_ends: int = 0
    connectivity_score: float = 0.0
    density_score: float = 0.0
    decoration_score: float = 0.0
    spawn_balance_score: float = 0.0
    architecture_score: float = 0.0


@dataclass
class ZoneQualityReport:
    zone_name: str
    category: ZoneCategory
    score: int
    metrics: ZoneMetrics = field(default_factory=ZoneMetrics)
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class MapQualityReport:
    map_name: str
    version: str
    overall_score: int
    zone_reports: List[ZoneQualityReport] = field(default_factory=list)
    global_issues: List[str] = field(default_factory=list)
    global_suggestions: List[str] = field(default_factory=list)
    metrics_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "map_name": self.map_name,
            "version": self.version,
            "overall_score": self.overall_score,
            "zones": [
                {
                    "zone": z.zone_name,
                    "category": z.category.value,
                    "score": z.score,
                    "issues": z.issues,
                    "suggestions": z.suggestions,
                }
                for z in self.zone_reports
            ],
            "global_issues": self.global_issues,
            "global_suggestions": self.global_suggestions,
            "metrics_summary": self.metrics_summary,
        }

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class QualityDetector:
    """
    Analyzes an OTBM map for quality across multiple dimensions:
      - Navigation (connectivity, dead ends, path flow)
      - Density (tile usage, spawn distribution, crowd balance)
      - Spawns (balance, variety, level-appropriateness)
      - Architecture (zone cohesion, transitions, structural integrity)
      - Decoration (ground variety, item placement, aesthetic appeal)

    Produces a MapQualityReport with per-zone scores and improvement suggestions.
    """

    # Thresholds for scoring
    MIN_DECORATION_PER_100_TILES = 15
    IDEAL_WALKABLE_RATIO = 0.60
    MAX_DEAD_ENDS_PER_ZONE = 2
    MIN_MONSTER_TYPES_PER_HUNT = 3
    MIN_SPAWNS_PER_HUNT_ZONE = 4
    IDEAL_GROUND_VARIETY = 5

    def __init__(self):
        self._zone_cache: Dict[str, ZoneQualityReport] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(
        self, otbm_data: Dict[str, Any], map_name: str = "unknown"
    ) -> MapQualityReport:
        """
        Full quality analysis of an OTBM map.

        Args:
            otbm_data: Deserialized OTBM structure (from OtbmDeserializer).
            map_name: Human-readable name for reporting.

        Returns:
            MapQualityReport with per-zone scores and global recommendations.
        """
        # 1. Partition the map into logical zones
        zones = self._partition_zones(otbm_data)

        # 2. Classify each zone
        classified = self._classify_zones(zones)

        # 3. Score each zone
        zone_reports = []
        for zone_name, (zone_data, category) in classified.items():
            metrics = self._compute_metrics(zone_data, category)
            score, issues, suggestions = self._score_zone(metrics, category)
            report = ZoneQualityReport(
                zone_name=zone_name,
                category=category,
                score=score,
                metrics=metrics,
                issues=issues,
                suggestions=suggestions,
            )
            zone_reports.append(report)
            self._zone_cache[zone_name] = report

        # 4. Compute global score and issues
        overall = self._compute_overall(zone_reports, otbm_data)

        return MapQualityReport(
            map_name=map_name,
            version=otbm_data.get("version", "unknown"),
            overall_score=overall["score"],
            zone_reports=zone_reports,
            global_issues=overall["global_issues"],
            global_suggestions=overall["global_suggestions"],
            metrics_summary=overall["summary"],
        )

    def get_zone_score(self, zone_name: str) -> Optional[int]:
        """Retrieve cached score for a specific zone."""
        report = self._zone_cache.get(zone_name)
        return report.score if report else None

    # ------------------------------------------------------------------
    # Zone partitioning
    # ------------------------------------------------------------------

    def _partition_zones(self, otbm_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Partition the OTBM map into logical zones.
        Uses spawn areas, town boundaries, and tile clustering as heuristics.
        """
        zones: Dict[str, Any] = {}
        map_data = otbm_data.get("map_data", otbm_data)

        # Extract towns as named zones
        towns = map_data.get("towns", [])
        for town in towns:
            name = town.get("name", f"town_{id(town)}")
            zones[name] = {
                "type": "town",
                "position": town.get("position", (0, 0, 0)),
                "temple_position": town.get("temple_position"),
                "tiles": [],
                "spawns": [],
            }

        # Extract spawn areas as zones
        spawns = map_data.get("spawns", [])
        for spawn in spawns:
            center = spawn.get("center_position", (0, 0, 0))
            radius = spawn.get("radius", 10)
            zone_name = spawn.get("name", f"spawn_{center}")
            zones[zone_name] = {
                "type": "spawn_area",
                "center": center,
                "radius": radius,
                "tiles": [],
                "spawns": spawn.get("monsters", []),
            }

        # Fallback: if no zones detected, treat the whole map as one zone
        if not zones:
            tiles = map_data.get("tiles", [])
            zones["full_map"] = {
                "type": "full_map",
                "tiles": tiles,
                "spawns": [],
            }

        # Distribute tiles to their nearest zone
        tiles = map_data.get("tiles", [])
        for tile in tiles:
            assigned = self._assign_tile_to_zone(tile, zones)
            if assigned:
                zones[assigned]["tiles"].append(tile)

        return zones

    def _assign_tile_to_zone(self, tile: Dict, zones: Dict[str, Any]) -> Optional[str]:
        """Assign a tile to the nearest zone by position."""
        tx, ty = tile.get("x", 0), tile.get("y", 0)
        best_zone = None
        best_dist = float("inf")

        for name, zone in zones.items():
            pos = zone.get("position") or zone.get("center")
            if pos is None:
                continue
            zx, zy = pos[0], pos[1]
            # Use Chebyshev distance for grid maps
            dist = max(abs(tx - zx), abs(ty - zy))
            radius = zone.get("radius", 30)
            if dist <= radius and dist < best_dist:
                best_dist = dist
                best_zone = name

        return best_zone

    # ------------------------------------------------------------------
    # Zone classification
    # ------------------------------------------------------------------

    def _classify_zones(
        self, zones: Dict[str, Any]
    ) -> Dict[str, Tuple[Any, ZoneCategory]]:
        """Classify each zone by its content patterns."""
        classified: Dict[str, Tuple[Any, ZoneCategory]] = {}

        for name, zone in zones.items():
            zone_type = zone.get("type", "unknown")
            spawns = zone.get("spawns", [])
            tiles = zone.get("tiles", [])

            if zone_type == "town":
                category = ZoneCategory.CITY
            elif zone_type == "spawn_area":
                # Check if it has boss-like spawns
                monster_names = [m.get("name", "") for m in spawns]
                if any(
                    "boss" in mn.lower()
                    or "lord" in mn.lower()
                    or "king" in mn.lower()
                    or "queen" in mn.lower()
                    for mn in monster_names
                ):
                    category = ZoneCategory.BOSS_ROOM
                elif len(monster_names) >= 4:
                    category = ZoneCategory.HUNT
                else:
                    category = ZoneCategory.CAVE
            elif len(tiles) < 20:
                category = ZoneCategory.TRANSITION
            elif not spawns and not any(t.get("items", []) for t in tiles):
                category = ZoneCategory.EMPTY
            else:
                category = ZoneCategory.WILDERNESS

            classified[name] = (zone, category)

        return classified

    # ------------------------------------------------------------------
    # Metrics computation
    # ------------------------------------------------------------------

    def _compute_metrics(
        self, zone_data: Dict[str, Any], category: ZoneCategory
    ) -> ZoneMetrics:
        """Compute raw metrics for a zone."""
        tiles = zone_data.get("tiles", [])
        spawns = zone_data.get("spawns", [])

        metrics = ZoneMetrics()
        metrics.tile_count = len(tiles)

        ground_ids: set = set()
        decoration_count = 0
        walkable = 0
        blocked = 0

        for tile in tiles:
            items = tile.get("items", [])
            if items:
                first_item = items[0]
                # Ground items typically have IDs in certain ranges
                item_id = first_item.get("id", 0)
                ground_ids.add(item_id)

            # Count decorations (items beyond the ground layer)
            decoration_count += max(0, len(items) - 1)

            # Walkability check via tile flags
            flags = tile.get("flags", 0)
            # TILESTATE_PROTECTIONZONE = 1, TILESTATE_NOPVPZONE = 2, etc.
            # Blocked tiles typically have certain flag patterns or PZ flags
            if flags & 1:  # Protection zone (towns, depots)
                walkable += 1
            elif flags & (1 << 5):  # TILESTATE_TRASHED / blocked
                blocked += 1
            elif len(items) > 0 and items[0].get("id", 0) > 0:
                walkable += 1
            else:
                blocked += 1

        metrics.walkable_tiles = walkable
        metrics.blocked_tiles = blocked
        metrics.ground_variety = len(ground_ids)
        metrics.decoration_count = decoration_count

        # Spawn metrics
        metrics.spawn_count = len(spawns)
        monster_names = set()
        for s in spawns:
            name = s.get("name", s.get("monster", ""))
            if name:
                monster_names.add(name)
        metrics.monster_types = len(monster_names)

        # Navigation heuristics
        metrics.navigation_nodes = self._count_navigation_nodes(tiles)
        metrics.dead_ends = self._count_dead_ends(tiles)
        metrics.connectivity_score = self._compute_connectivity(tiles)
        metrics.density_score = self._compute_density(metrics)
        metrics.decoration_score = self._compute_decoration_score(metrics)
        metrics.spawn_balance_score = self._compute_spawn_balance(metrics, category)
        metrics.architecture_score = self._compute_architecture_score(metrics, category)

        return metrics

    def _count_navigation_nodes(self, tiles: List[Dict]) -> int:
        """Estimate navigation nodes: tiles with 3+ walkable neighbors (intersections)."""
        if not tiles:
            return 0
        tile_set = {(t.get("x", 0), t.get("y", 0)) for t in tiles}
        nodes = 0
        for tx, ty in tile_set:
            neighbors = sum(
                1
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]
                if (tx + dx, ty + dy) in tile_set
            )
            if neighbors >= 3:
                nodes += 1
        return nodes

    def _count_dead_ends(self, tiles: List[Dict]) -> int:
        """Count dead ends: tiles with exactly 1 walkable neighbor."""
        if not tiles:
            return 0
        tile_set = {(t.get("x", 0), t.get("y", 0)) for t in tiles}
        dead_ends = 0
        for tx, ty in tile_set:
            neighbors = sum(
                1
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]
                if (tx + dx, ty + dy) in tile_set
            )
            if neighbors == 1:
                dead_ends += 1
        return dead_ends

    def _compute_connectivity(self, tiles: List[Dict]) -> float:
        """Score 0-100: how well connected the zone's tiles are."""
        if not tiles:
            return 0.0
        tile_set = {(t.get("x", 0), t.get("y", 0)) for t in tiles}
        total_connections = 0
        for tx, ty in tile_set:
            neighbors = sum(
                1
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]
                if (tx + dx, ty + dy) in tile_set
            )
            total_connections += neighbors
        max_possible = len(tile_set) * 4
        return (total_connections / max(max_possible, 1)) * 100

    def _compute_density(self, metrics: ZoneMetrics) -> float:
        """Score 0-100: density of meaningful content vs empty space."""
        if metrics.tile_count == 0:
            return 0.0
        walkable_ratio = metrics.walkable_tiles / max(metrics.tile_count, 1)
        # Penalize extremes: too empty or too crowded
        ideal = self.IDEAL_WALKABLE_RATIO
        deviation = abs(walkable_ratio - ideal)
        base = max(0, 100 - deviation * 100)
        return round(base, 1)

    def _compute_decoration_score(self, metrics: ZoneMetrics) -> float:
        """Score 0-100: aesthetic quality based on decoration density and ground variety."""
        if metrics.tile_count == 0:
            return 0.0
        decor_per_100 = (metrics.decoration_count / metrics.tile_count) * 100
        decor_score = min(
            100, (decor_per_100 / max(self.MIN_DECORATION_PER_100_TILES, 1)) * 100
        )
        ground_score = min(
            100, (metrics.ground_variety / max(self.IDEAL_GROUND_VARIETY, 1)) * 100
        )
        return round((decor_score * 0.6 + ground_score * 0.4), 1)

    def _compute_spawn_balance(
        self, metrics: ZoneMetrics, category: ZoneCategory
    ) -> float:
        """Score 0-100: spawn distribution quality."""
        if category in (ZoneCategory.CITY, ZoneCategory.TRANSITION, ZoneCategory.EMPTY):
            return 100.0  # N/A for non-hunt zones
        if metrics.spawn_count == 0:
            return 0.0
        type_score = min(
            100, (metrics.monster_types / max(self.MIN_MONSTER_TYPES_PER_HUNT, 1)) * 100
        )
        count_score = min(
            100, (metrics.spawn_count / max(self.MIN_SPAWNS_PER_HUNT_ZONE, 1)) * 100
        )
        return round((type_score * 0.5 + count_score * 0.5), 1)

    def _compute_architecture_score(
        self, metrics: ZoneMetrics, category: ZoneCategory
    ) -> float:
        """Score 0-100: structural integrity of the zone layout."""
        dead_end_penalty = max(0, metrics.dead_ends - self.MAX_DEAD_ENDS_PER_ZONE) * 5
        base = 70.0  # Default decent architecture
        base += metrics.connectivity_score * 0.2
        base -= dead_end_penalty
        return round(max(0, min(100, base)), 1)

    # ------------------------------------------------------------------
    # Zone scoring
    # ------------------------------------------------------------------

    def _score_zone(
        self, metrics: ZoneMetrics, category: ZoneCategory
    ) -> Tuple[int, List[str], List[str]]:
        """
        Compute a 0-100 score for a zone and generate issues/suggestions.
        Weights depend on zone category.
        """
        weights = self._get_weights(category)
        scores = {
            "navigation": metrics.connectivity_score * weights["navigation"],
            "density": metrics.density_score * weights["density"],
            "spawns": metrics.spawn_balance_score * weights["spawns"],
            "architecture": metrics.architecture_score * weights["architecture"],
            "decoration": metrics.decoration_score * weights["decoration"],
        }
        total_weight = sum(weights.values()) or 1
        raw_score = sum(scores.values()) / total_weight

        issues, suggestions = self._generate_feedback(metrics, category, scores)
        return int(round(raw_score)), issues, suggestions

    def _get_weights(self, category: ZoneCategory) -> Dict[str, float]:
        """Get scoring weights per dimension based on zone category."""
        base = {
            "city": {
                "navigation": 0.25,
                "density": 0.20,
                "spawns": 0.05,
                "architecture": 0.25,
                "decoration": 0.25,
            },
            "hunt": {
                "navigation": 0.20,
                "density": 0.15,
                "spawns": 0.35,
                "architecture": 0.15,
                "decoration": 0.15,
            },
            "boss_room": {
                "navigation": 0.10,
                "density": 0.10,
                "spawns": 0.40,
                "architecture": 0.25,
                "decoration": 0.15,
            },
            "quest_zone": {
                "navigation": 0.25,
                "density": 0.15,
                "spawns": 0.20,
                "architecture": 0.25,
                "decoration": 0.15,
            },
            "cave": {
                "navigation": 0.30,
                "density": 0.20,
                "spawns": 0.25,
                "architecture": 0.15,
                "decoration": 0.10,
            },
            "wilderness": {
                "navigation": 0.20,
                "density": 0.20,
                "spawns": 0.25,
                "architecture": 0.15,
                "decoration": 0.20,
            },
            "transition": {
                "navigation": 0.40,
                "density": 0.20,
                "spawns": 0.05,
                "architecture": 0.20,
                "decoration": 0.15,
            },
            "empty": {
                "navigation": 0.30,
                "density": 0.25,
                "spawns": 0.05,
                "architecture": 0.20,
                "decoration": 0.20,
            },
        }
        return base.get(category.value, base["wilderness"])

    def _generate_feedback(
        self, metrics: ZoneMetrics, category: ZoneCategory, scores: Dict[str, float]
    ) -> Tuple[List[str], List[str]]:
        """Generate human-readable issues and suggestions from metrics."""
        issues: List[str] = []
        suggestions: List[str] = []

        # Navigation
        if metrics.connectivity_score < 40:
            issues.append(f"Low connectivity ({metrics.connectivity_score:.0f}/100)")
            suggestions.append("Add hallways or bridges to improve connectivity")
        if metrics.dead_ends > self.MAX_DEAD_ENDS_PER_ZONE:
            issues.append(f"Too many dead ends ({metrics.dead_ends})")
            suggestions.append("Convert dead-end alleys into connected hallways")

        # Density
        if metrics.density_score < 50:
            issues.append(f"Low content density ({metrics.density_score:.0f}/100)")
            suggestions.append("Add more walkable tiles or playable content")
        if metrics.density_score > 95:
            issues.append("Excessive density — saturated map")
            suggestions.append("Open up spaces; consider expanding the zone")

        # Spawns
        if category in (ZoneCategory.HUNT, ZoneCategory.CAVE, ZoneCategory.BOSS_ROOM):
            if metrics.monster_types < self.MIN_MONSTER_TYPES_PER_HUNT:
                issues.append(f"Few monster types ({metrics.monster_types})")
                suggestions.append(
                    f"Add at least {self.MIN_MONSTER_TYPES_PER_HUNT - metrics.monster_types} additional monster type(s)"
                )
            if metrics.spawn_count < self.MIN_SPAWNS_PER_HUNT_ZONE:
                issues.append(f"Few spawns ({metrics.spawn_count})")
                suggestions.append(
                    f"Add at least {self.MIN_SPAWNS_PER_HUNT_ZONE - metrics.spawn_count} more spawn(s)"
                )

        # Decoration
        if metrics.decoration_score < 40:
            issues.append(f"Poor decoration ({metrics.decoration_score:.0f}/100)")
            suggestions.append(
                "Add more decorative elements: torches, statues, carpets, etc."
            )
        if metrics.ground_variety < 3:
            issues.append(f"Low ground variety ({metrics.ground_variety} types)")
            suggestions.append("Vary ground tiles to improve aesthetics")

        # Architecture
        if metrics.architecture_score < 50:
            issues.append(
                f"Architectural problems ({metrics.architecture_score:.0f}/100)"
            )
            suggestions.append(
                "Review overall structure: shapes, transitions, and coherence"
            )

        return issues, suggestions

    # ------------------------------------------------------------------
    # Overall scoring
    # ------------------------------------------------------------------

    def _compute_overall(
        self, zone_reports: List[ZoneQualityReport], otbm_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compute global score and cross-zone issues."""
        if not zone_reports:
            return {
                "score": 0,
                "global_issues": ["Empty map"],
                "global_suggestions": ["Create content from scratch"],
                "summary": {},
            }

        avg_score = sum(r.score for r in zone_reports) / len(zone_reports)

        global_issues: List[str] = []
        global_suggestions: List[str] = []

        # Check for empty zones
        empty_zones = [
            r.zone_name for r in zone_reports if r.category == ZoneCategory.EMPTY
        ]
        if empty_zones:
            global_issues.append(f"Empty zones detected: {', '.join(empty_zones)}")
            global_suggestions.append(
                "Fill empty zones with hunts, quests, or decoration"
            )

        # Check city presence
        has_city = any(r.category == ZoneCategory.CITY for r in zone_reports)
        if not has_city:
            global_issues.append("No city detected")
            global_suggestions.append(
                "Add at least one city with temple, depot, and NPCs"
            )

        # Check hunt balance
        hunt_zones = [r for r in zone_reports if r.category == ZoneCategory.HUNT]
        if hunt_zones:
            hunt_scores = [r.score for r in hunt_zones]
            if max(hunt_scores) - min(hunt_scores) > 40:
                global_issues.append(
                    "Unbalanced hunts: large quality difference between zones"
                )
                global_suggestions.append(
                    "Level hunt quality for a consistent experience"
                )

        # Boss room check
        has_boss = any(r.category == ZoneCategory.BOSS_ROOM for r in zone_reports)
        if not has_boss and len(zone_reports) > 3:
            global_suggestions.append(
                "Consider adding a boss room for end-game content"
            )

        # Quest zone check
        has_quest = any(r.category == ZoneCategory.QUEST_ZONE for r in zone_reports)
        if not has_quest and len(zone_reports) > 3:
            global_suggestions.append("Consider adding quest zones for progression")

        summary = {
            "total_zones": len(zone_reports),
            "zone_categories": {
                cat.value: sum(1 for r in zone_reports if r.category.value == cat.value)
                for cat in ZoneCategory
            },
            "avg_zone_score": round(avg_score, 1),
            "min_zone_score": min(r.score for r in zone_reports),
            "max_zone_score": max(r.score for r in zone_reports),
            "empty_zone_count": len(empty_zones),
        }

        return {
            "score": int(round(avg_score)),
            "global_issues": global_issues,
            "global_suggestions": global_suggestions,
            "summary": summary,
        }
