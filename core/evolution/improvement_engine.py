from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from .quality_detector import (
    QualityDetector,
    ZoneQualityReport,
    ZoneCategory,
    MapQualityReport,
)


class ImprovementType(Enum):
    ADD_PATHS = "add_paths"
    CREATE_SHORTCUTS = "create_shortcuts"
    REORGANIZE_SPAWNS = "reorganize_spawns"
    EXPAND_HUNTS = "expand_hunts"
    ADD_DECORATION = "add_decoration"
    FILL_EMPTY_ZONES = "fill_empty_zones"
    BALANCE_DENSITY = "balance_density"
    IMPROVE_CONNECTIVITY = "improve_connectivity"
    ADD_TRANSITIONS = "add_transitions"


@dataclass
class ImprovementPlan:
    zone_name: str
    category: ZoneCategory
    current_score: int
    target_score: int
    improvements: List[ImprovementType] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_name": self.zone_name,
            "category": self.category.value,
            "current_score": self.current_score,
            "target_score": self.target_score,
            "improvements": [i.value for i in self.improvements],
            "details": self.details,
        }


@dataclass
class ImprovementResult:
    improved_data: Dict[str, Any]
    plans_executed: List[ImprovementPlan]
    score_before: int
    score_after: int
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plans": [p.to_dict() for p in self.plans_executed],
            "score_before": self.score_before,
            "score_after": self.score_after,
            "summary": self.summary,
        }


class ImprovementEngine:
    """
    Applies targeted improvements to an OTBM map based on quality analysis.

    Capabilities:
      - Add paths / corridors between disconnected zones
      - Create shortcuts to reduce backtracking
      - Reorganize spawns for better balance and progression
      - Expand hunt areas with additional rooms
      - Add decoration to barren zones
      - Fill empty zones with procedural content
      - Balance tile density across the map
      - Improve connectivity by connecting dead ends
    """

    PATH_GROUND_IDS = {
        "stone": 1284,
        "gravel": 1294,
        "wooden": 420,
        "cobblestone": 231,
        "sand": 231,
        "dirt": 102,
    }

    DECORATION_IDS = {
        "torch": 2050,
        "wall_torch": 2052,
        "statue": 1510,
        "pillar": 1545,
        "barrel": 1775,
        "crate": 1738,
        "bush": 2705,
        "small_stone": 1304,
        "flower": 2104,
    }

    def __init__(self):
        self.quality_detector = QualityDetector()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def improve(self, otbm_data: Dict[str, Any], map_name: str = "unknown",
                target_score: int = 85) -> ImprovementResult:
        """Analyze and improve an OTBM map, targeting a minimum quality score."""
        report = self.quality_detector.analyze(otbm_data, map_name)
        score_before = report.overall_score

        plans = self._generate_plans(report, target_score)

        improved_data = otbm_data
        executed_plans = []
        for plan in plans:
            improved_data = self._execute_plan(plan, improved_data)
            executed_plans.append(plan)

        new_report = self.quality_detector.analyze(improved_data, f"{map_name}_v2")
        score_after = new_report.overall_score

        score_delta = score_after - score_before
        summary = (
            f"Mejora completada: {score_before} → {score_after} "
            f"({'+' if score_delta >= 0 else ''}{score_delta} pts). "
            f"{len(executed_plans)} zonas mejoradas."
        )

        return ImprovementResult(
            improved_data=improved_data,
            plans_executed=executed_plans,
            score_before=score_before,
            score_after=score_after,
            summary=summary,
        )

    # ------------------------------------------------------------------
    # Plan generation
    # ------------------------------------------------------------------

    def _generate_plans(self, report: MapQualityReport, target_score: int) -> List[ImprovementPlan]:
        """Generate prioritized improvement plans for zones below target."""
        plans: List[ImprovementPlan] = []

        for zone in report.zone_reports:
            if zone.score >= target_score:
                continue

            plan = ImprovementPlan(
                zone_name=zone.zone_name,
                category=zone.category,
                current_score=zone.score,
                target_score=target_score,
            )

            for issue in zone.issues:
                lower = issue.lower()
                if "conectividad" in lower or "callejones" in lower:
                    plan.improvements.append(ImprovementType.IMPROVE_CONNECTIVITY)
                    plan.improvements.append(ImprovementType.CREATE_SHORTCUTS)
                if "densidad" in lower:
                    plan.improvements.append(ImprovementType.BALANCE_DENSITY)
                if "spawn" in lower or "monstruo" in lower:
                    plan.improvements.append(ImprovementType.REORGANIZE_SPAWNS)
                if "decoración" in lower or "suelo" in lower:
                    plan.improvements.append(ImprovementType.ADD_DECORATION)

            if zone.category == ZoneCategory.HUNT:
                plan.improvements.append(ImprovementType.EXPAND_HUNTS)
            elif zone.category == ZoneCategory.EMPTY:
                plan.improvements.append(ImprovementType.FILL_EMPTY_ZONES)
                plan.improvements.append(ImprovementType.ADD_PATHS)
            elif zone.category == ZoneCategory.TRANSITION:
                plan.improvements.append(ImprovementType.ADD_TRANSITIONS)

            seen: Set[ImprovementType] = set()
            plan.improvements = [i for i in plan.improvements if not (i in seen or seen.add(i))]

            plan.details = {
                "metrics": {
                    "tile_count": zone.metrics.tile_count,
                    "walkable_tiles": zone.metrics.walkable_tiles,
                    "ground_variety": zone.metrics.ground_variety,
                    "decoration_count": zone.metrics.decoration_count,
                    "spawn_count": zone.metrics.spawn_count,
                    "monster_types": zone.metrics.monster_types,
                    "dead_ends": zone.metrics.dead_ends,
                    "connectivity_score": zone.metrics.connectivity_score,
                },
                "suggestions": zone.suggestions,
            }

            plans.append(plan)

        plans.sort(key=lambda p: p.current_score)
        return plans

    # ------------------------------------------------------------------
    # Plan execution
    # ------------------------------------------------------------------

    def _execute_plan(self, plan: ImprovementPlan, otbm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single improvement plan on the OTBM data."""
        data = otbm_data
        for improvement in plan.improvements:
            handler = self._get_handler(improvement)
            if handler:
                data = handler(data, plan)
        return data

    def _get_handler(self, improvement: ImprovementType):
        handlers = {
            ImprovementType.ADD_PATHS: self._add_paths,
            ImprovementType.CREATE_SHORTCUTS: self._create_shortcuts,
            ImprovementType.REORGANIZE_SPAWNS: self._reorganize_spawns,
            ImprovementType.EXPAND_HUNTS: self._expand_hunts,
            ImprovementType.ADD_DECORATION: self._add_decoration,
            ImprovementType.FILL_EMPTY_ZONES: self._fill_empty_zone,
            ImprovementType.BALANCE_DENSITY: self._balance_density,
            ImprovementType.IMPROVE_CONNECTIVITY: self._improve_connectivity,
            ImprovementType.ADD_TRANSITIONS: self._add_transitions,
        }
        return handlers.get(improvement)

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _get_tiles(self, data: Dict[str, Any]) -> List[Dict]:
        """Extract tiles list from OTBM data."""
        map_data = data.get("map_data", data)
        return map_data.get("tiles", [])

    def _set_tiles(self, data: Dict[str, Any], tiles: List[Dict]) -> Dict[str, Any]:
        """Set tiles list back into OTBM data."""
        if "map_data" in data:
            data["map_data"]["tiles"] = tiles
        else:
            data["tiles"] = tiles
        return data

    def _get_spawns(self, data: Dict[str, Any]) -> List[Dict]:
        """Extract spawns list from OTBM data."""
        map_data = data.get("map_data", data)
        return map_data.get("spawns", [])

    def _set_spawns(self, data: Dict[str, Any], spawns: List[Dict]) -> Dict[str, Any]:
        """Set spawns list back into OTBM data."""
        if "map_data" in data:
            data["map_data"]["spawns"] = spawns
        else:
            data["spawns"] = spawns
        return data

    def _find_disconnected_clusters(self, tile_set: Set[Tuple[int, int]]) -> List[Set[Tuple[int, int]]]:
        """Find disconnected clusters of tiles using BFS."""
        visited: Set[Tuple[int, int]] = set()
        clusters: List[Set[Tuple[int, int]]] = []

        for tile in tile_set:
            if tile in visited:
                continue
            cluster: Set[Tuple[int, int]] = set()
            queue = [tile]
            while queue:
                cx, cy = queue.pop(0)
                if (cx, cy) in visited:
                    continue
                visited.add((cx, cy))
                cluster.add((cx, cy))
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    neighbor = (cx + dx, cy + dy)
                    if neighbor in tile_set and neighbor not in visited:
                        queue.append(neighbor)
            clusters.append(cluster)

        return clusters

    def _closest_points(self, cluster_a: Set[Tuple[int, int]],
                        cluster_b: Set[Tuple[int, int]]) -> Tuple[Optional[Tuple[int, int]], Optional[Tuple[int, int]]]:
        """Find the two closest points between two clusters."""
        best_a = None
        best_b = None
        best_dist = float("inf")

        for a in cluster_a:
            for b in cluster_b:
                dist = abs(a[0] - b[0]) + abs(a[1] - b[1])
                if dist < best_dist:
                    best_dist = dist
                    best_a = a
                    best_b = b

        return best_a, best_b

    def _bresenham_path(self, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Generate a path between two points using Bresenham's line algorithm."""
        x1, y1 = start
        x2, y2 = end
        points = []

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            points.append((x1, y1))
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

        return points

    # ------------------------------------------------------------------
    # Improvement handlers
    # ------------------------------------------------------------------

    def _add_paths(self, data: Dict[str, Any], _plan: ImprovementPlan) -> Dict[str, Any]:
        """Add path corridors to improve zone connectivity."""
        tiles = self._get_tiles(data)
        if not tiles:
            return data

        tile_set = {(t.get("x", 0), t.get("y", 0)) for t in tiles}
        clusters = self._find_disconnected_clusters(tile_set)

        if len(clusters) < 2:
            return data

        c1 = max(clusters, key=len)
        clusters.remove(c1)
        c2 = max(clusters, key=len)
        clusters.remove(c2)

        p1, p2 = self._closest_points(c1, c2)
        if p1 and p2:
            path_tiles = self._bresenham_path(p1, p2)
            path_ground_id = self.PATH_GROUND_IDS["cobblestone"]

            for px, py in path_tiles:
                if (px, py) not in tile_set:
                    new_tile = {
                        "x": px,
                        "y": py,
                        "z": 7,
                        "items": [{"id": path_ground_id, "count": 1}],
                        "flags": 0,
                    }
                    tiles.append(new_tile)
                    tile_set.add((px, py))

            return self._set_tiles(data, tiles)
        return data

    def _create_shortcuts(self, data: Dict[str, Any], plan: ImprovementPlan) -> Dict[str, Any]:
        """Create shortcuts by connecting dead ends to nearby paths."""
        tiles = self._get_tiles(data)
        if not tiles:
            return data

        tile_set = {(t.get("x", 0), t.get("y", 0)) for t in tiles}

        # Find dead ends
        dead_ends = []
        for tx, ty in tile_set:
            neighbors = sum(
                1 for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]
                if (tx + dx, ty + dy) in tile_set
            )
            if neighbors == 1:
                dead_ends.append((tx, ty))

        max_shortcuts = 3
        shortcuts_added = 0

        for dx, dy in dead_ends:
            if shortcuts_added >= max_shortcuts:
                break
            # Try to find a nearby tile in a different direction to connect
            for sdx, sdy in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
                target = (dx + sdx, dy + sdy)
                if target in tile_set and (dx + sdx // 2, dy + sdy // 2) not in tile_set:
                    mid_x, mid_y = dx + sdx // 2, dy + sdy // 2
                    new_tile = {
                        "x": mid_x,
                        "y": mid_y,
                        "z": 7,
                        "items": [{"id": self.PATH_GROUND_IDS["stone"], "count": 1}],
                        "flags": 0,
                    }
                    tiles.append(new_tile)
                    tile_set.add((mid_x, mid_y))
                    shortcuts_added += 1
                    break

        return self._set_tiles(data, tiles)

    def _reorganize_spawns(self, data: Dict[str, Any], plan: ImprovementPlan) -> Dict[str, Any]:
        """Reorganize spawns for better distribution and variety."""
        spawns = self._get_spawns(data)
        if not spawns:
            return data

        monster_types_needed = max(0, 3 - len({s.get("name", "") for s in spawns}))
        spawns_needed = max(0, 4 - len(spawns))

        # Add variety to existing spawns
        default_monsters = ["Rat", "Cave Rat", "Troll", "Orc", "Minotaur", "Cyclops"]
        for i in range(monster_types_needed):
            idx = i % len(default_monsters)
            for spawn in spawns:
                spawn["monsters"] = spawn.get("monsters", [])
                if len(spawn["monsters"]) < 2:
                    spawn["monsters"].append({"name": default_monsters[idx], "count": 2})

        # Add new spawn points if needed
        tiles = self._get_tiles(data)
        if tiles and spawns_needed > 0:
            for i in range(spawns_needed):
                center_tile = tiles[len(tiles) // (i + 2)] if tiles else {"x": 10 + i * 5, "y": 10 + i * 5}
                new_spawn = {
                    "name": f"spawn_improved_{i + 1}",
                    "center_position": (center_tile.get("x", 10), center_tile.get("y", 10), 7),
                    "radius": 8,
                    "monsters": [{"name": default_monsters[i % len(default_monsters)], "count": 2}],
                }
                spawns.append(new_spawn)

        return self._set_spawns(data, spawns)

    def _expand_hunts(self, data: Dict[str, Any], plan: ImprovementPlan) -> Dict[str, Any]:
        """Expand hunt areas by adding adjacent rooms."""
        tiles = self._get_tiles(data)
        if not tiles:
            return data

        tile_set = {(t.get("x", 0), t.get("y", 0)) for t in tiles}

        # Find the bounding box of existing tiles
        min_x = min(t[0] for t in tile_set) if tile_set else 0
        max_x = max(t[0] for t in tile_set) if tile_set else 0
        min_y = min(t[1] for t in tile_set) if tile_set else 0
        max_y = max(t[1] for t in tile_set) if tile_set else 0

        # Expand to the east with a new room
        room_width = 5
        room_height = 5
        offset_x = max_x + 3
        offset_y = min_y + (max_y - min_y) // 2 - room_height // 2

        # Create corridor from existing area to new room
        corridor_start = (max_x, offset_y + room_height // 2)
        corridor_end = (offset_x, offset_y + room_height // 2)
        corridor = self._bresenham_path(corridor_start, corridor_end)

        for cx, cy in corridor:
            if (cx, cy) not in tile_set:
                tiles.append({
                    "x": cx, "y": cy, "z": 7,
                    "items": [{"id": self.PATH_GROUND_IDS["stone"], "count": 1}],
                    "flags": 0,
                })
                tile_set.add((cx, cy))

        # Create the new room
        for rx in range(offset_x, offset_x + room_width):
            for ry in range(offset_y, offset_y + room_height):
                if (rx, ry) not in tile_set:
                    tiles.append({
                        "x": rx, "y": ry, "z": 7,
                        "items": [{"id": self.PATH_GROUND_IDS["dirt"], "count": 1}],
                        "flags": 0,
                    })
                    tile_set.add((rx, ry))

        return self._set_tiles(data, tiles)

    def _add_decoration(self, data: Dict[str, Any], plan: ImprovementPlan) -> Dict[str, Any]:
        """Add decorative items to barren tiles."""
        tiles = self._get_tiles(data)
        if not tiles:
            return data

        decor_keys = list(self.DECORATION_IDS.keys())
        decor_count = max(1, len(tiles) // 10)

        import random
        for i in range(min(decor_count, len(tiles))):
            tile_idx = (i * 7 + 3) % len(tiles)
            tile = tiles[tile_idx]
            tile["items"] = tile.get("items", [])
            decor_key = decor_keys[i % len(decor_keys)]
            tile["items"].append({"id": self.DECORATION_IDS[decor_key], "count": 1})

        return self._set_tiles(data, tiles)

    def _fill_empty_zone(self, data: Dict[str, Any], plan: ImprovementPlan) -> Dict[str, Any]:
        """Fill an empty zone with basic content."""
        tiles = self._get_tiles(data)

        # Use details to determine zone bounds
        details = plan.details.get("metrics", {})
        base_x = 50
        base_y = 50
        width = 10
        height = 10

        for x in range(base_x, base_x + width):
            for y in range(base_y, base_y + height):
                tiles.append({
                    "x": x, "y": y, "z": 7,
                    "items": [
                        {"id": self.PATH_GROUND_IDS["dirt"], "count": 1},
                        {"id": self.DECORATION_IDS["small_stone"], "count": 1},
                    ] if (x + y) % 3 == 0 else [{"id": self.PATH_GROUND_IDS["dirt"], "count": 1}],
                    "flags": 0,
                })

        # Add some spawns
        spawns = self._get_spawns(data)
        spawns.append({
            "name": f"filled_zone_{plan.zone_name}",
            "center_position": (base_x + width // 2, base_y + height // 2, 7),
            "radius": 8,
            "monsters": [{"name": "Troll", "count": 3}, {"name": "Orc", "count": 2}],
        })

        data = self._set_spawns(data, spawns)
        return self._set_tiles(data, tiles)

    def _balance_density(self, data: Dict[str, Any], plan: ImprovementPlan) -> Dict[str, Any]:
        """Balance tile density by opening blocked areas or filling sparse ones."""
        tiles = self._get_tiles(data)
        if not tiles:
            return data

        walkable = sum(1 for t in tiles if t.get("flags", 0) == 0 or t.get("flags", 0) & 1)
        total = len(tiles)
        if total == 0:
            return data

        ratio = walkable / total

        if ratio < 0.4:
            # Too blocked: unblock some tiles
            for tile in tiles:
                if tile.get("flags", 0) > 0 and not (tile.get("flags", 0) & 1):
                    tile["flags"] = 0
        elif ratio > 0.8:
            # Too open: add some blocking (walls) at edges
            tile_set = {(t.get("x", 0), t.get("y", 0)) for t in tiles}
            blocked = 0
            for tx, ty in list(tile_set):
                neighbors = sum(
                    1 for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]
                    if (tx + dx, ty + dy) in tile_set
                )
                if neighbors <= 2 and blocked < 5:
                    tiles.append({
                        "x": tx + 1, "y": ty,
                        "z": 7,
                        "items": [{"id": 1000, "count": 1}],  # Wall item
                        "flags": 64,
                    })
                    blocked += 1

        return self._set_tiles(data, tiles)

    def _improve_connectivity(self, data: Dict[str, Any], plan: ImprovementPlan) -> Dict[str, Any]:
        """Improve connectivity by filling gaps and removing isolated tiles."""
        tiles = self._get_tiles(data)
        if not tiles:
            return data

        tile_set = {(t.get("x", 0), t.get("y", 0)) for t in tiles}

        # Fill single-tile gaps between walkable tiles
        gaps_filled = 0
        for tx, ty in list(tile_set):
            if gaps_filled >= 10:
                break
            for dx, dy in [(0, 2), (2, 0), (0, -2), (-2, 0)]:
                nx, ny = tx + dx, ty + dy
                mx, my = tx + dx // 2, ty + dy // 2
                if (nx, ny) in tile_set and (mx, my) not in tile_set:
                    tiles.append({
                        "x": mx, "y": my, "z": 7,
                        "items": [{"id": self.PATH_GROUND_IDS["gravel"], "count": 1}],
                        "flags": 0,
                    })
                    tile_set.add((mx, my))
                    gaps_filled += 1
                    break

        return self._set_tiles(data, tiles)

    def _add_transitions(self, data: Dict[str, Any], plan: ImprovementPlan) -> Dict[str, Any]:
        """Add transition tiles (stairs, ladders, teleports) between levels."""
        tiles = self._get_tiles(data)
        if not tiles:
            return data

        tile_set = {(t.get("x", 0), t.get("y", 0), t.get("z", 7)) for t in tiles}

        # Find a good location for a transition
        if tiles:
            mid = tiles[len(tiles) // 2]
            tx, ty, tz = mid.get("x", 10), mid.get("y", 10), mid.get("z", 7)

            # Add a stair tile going up
            tiles.append({
                "x": tx + 1, "y": ty + 1, "z": tz,
                "items": [
                    {"id": self.PATH_GROUND_IDS["stone"], "count": 1},
                    {"id": 1386, "count": 1},  # Ladder / stair item
                ],
                "flags": 0,
            })

            # Add corresponding tile on the level above
            tiles.append({
                "x": tx + 1, "y": ty + 1, "z": tz - 1,
                "items": [
                    {"id": self.PATH_GROUND_IDS["stone"], "count": 1},
                    {"id": 1386, "count": 1},
                ],
                "flags": 0,
            })

        return self._set_tiles(data, tiles)