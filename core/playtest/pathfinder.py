"""
A* Pathfinder for WorldModel traversal.

Finds optimal paths through generated worlds, handling multi-floor navigation,
obstacles, and zone transitions. Used by the playtest engine to simulate
real player movement.
"""

from __future__ import annotations

import heapq
import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class PathResult:
    """Result of a pathfinding query."""

    waypoints: List[Tuple[int, int, int]]
    distance: float
    steps: int
    floors_traversed: int
    reachable: bool
    blocked_tiles: int = 0

    @property
    def total_distance(self) -> float:
        return self.distance


@dataclass
class _Node:
    """Internal A* node."""

    x: int
    y: int
    z: int
    g: float = 0.0
    h: float = 0.0
    f: float = 0.0
    parent: Optional[_Node] = None

    def __lt__(self, other: _Node) -> bool:
        return self.f < other.f

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _Node):
            return NotImplemented
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __hash__(self) -> int:
        return hash((self.x, self.y, self.z))


class Pathfinder:
    """A* pathfinder over a WorldModel tile grid."""

    DIRECTIONS_8: List[Tuple[int, int]] = [
        (0, 1),
        (0, -1),
        (1, 0),
        (-1, 0),
        (1, 1),
        (1, -1),
        (-1, 1),
        (-1, -1),
    ]

    DIRECTIONS_4: List[Tuple[int, int]] = [
        (0, 1),
        (0, -1),
        (1, 0),
        (-1, 0),
    ]

    Z_STEPS: List[int] = [-1, 1]

    MOVE_COST_CARDINAL = 1.0
    MOVE_COST_DIAGONAL = 1.414
    STAIR_COST = 3.0
    SPAWN_PENALTY = 0.5

    def __init__(self, world, diagonal: bool = True, use_stairs: bool = True):
        """
        Args:
            world: WorldModel instance
            diagonal: Allow diagonal movement
            use_stairs: Allow floor transitions via stairs/teleports
        """
        self._world = world
        self._diagonal = diagonal
        self._use_stairs = use_stairs
        self._directions = self.DIRECTIONS_8 if diagonal else self.DIRECTIONS_4
        self._tile_cache: Dict[str, object] = {}

    def _get_tile(self, x: int, y: int, z: int):
        """Get tile from world, with caching."""
        key = f"{x}:{y}:{z}"
        if key not in self._tile_cache:
            self._tile_cache[key] = self._world.get_tile(x, y, z)
        return self._tile_cache[key]

    def _is_walkable(self, x: int, y: int, z: int) -> bool:
        """Check if a tile exists and is walkable (has ground)."""
        tile = self._get_tile(x, y, z)
        if tile is None:
            return False
        # Tiles with a ground ID or items are walkable
        if tile.ground is not None:
            return True
        if tile.items:
            return True
        return False

    def _has_spawn(self, x: int, y: int, z: int) -> bool:
        """Check if a tile has a monster spawn."""
        tile = self._get_tile(x, y, z)
        if tile is None:
            return False
        return tile.spawn is not None

    def _move_cost(
        self, from_x: int, from_y: int, from_z: int, to_x: int, to_y: int, to_z: int
    ) -> float:
        """Calculate movement cost between two adjacent tiles."""
        dx = abs(to_x - from_x)
        dy = abs(to_y - from_y)
        dz = abs(to_z - from_z)

        # Floor transition
        if dz > 0:
            return self.STAIR_COST

        # Diagonal movement
        if dx + dy == 2:
            cost = self.MOVE_COST_DIAGONAL
        else:
            cost = self.MOVE_COST_CARDINAL

        # Spawn penalty
        if self._has_spawn(to_x, to_y, to_z):
            cost += self.SPAWN_PENALTY

        return cost

    def _heuristic(self, ax: int, ay: int, az: int, bx: int, by: int, bz: int) -> float:
        """Octile distance heuristic (matches 8-directional movement)."""
        dx = abs(ax - bx)
        dy = abs(ay - by)
        dz = abs(az - bz)
        # Use octile distance for XY plane + stair cost for Z
        h = max(dx, dy) + (min(dx, dy) * 0.414)
        h += dz * self.STAIR_COST
        return h

    def find_path(
        self,
        start: Tuple[int, int, int],
        goal: Tuple[int, int, int],
        max_iterations: int = 50000,
    ) -> PathResult:
        """
        Find shortest path from start to goal using A*.

        Args:
            start: (x, y, z) starting position
            goal: (x, y, z) target position
            max_iterations: Safety limit to prevent infinite loops

        Returns:
            PathResult with waypoints, distance, and metadata
        """
        sx, sy, sz = start
        gx, gy, gz = goal

        # Quick check: start and goal must exist
        if not self._is_walkable(sx, sy, sz):
            return PathResult(
                waypoints=[],
                distance=0.0,
                steps=0,
                floors_traversed=0,
                reachable=False,
                blocked_tiles=1,
            )
        if not self._is_walkable(gx, gy, gz):
            return PathResult(
                waypoints=[],
                distance=0.0,
                steps=0,
                floors_traversed=0,
                reachable=False,
                blocked_tiles=1,
            )

        # Already at goal
        if start == goal:
            return PathResult(
                waypoints=[start],
                distance=0.0,
                steps=0,
                floors_traversed=0,
                reachable=True,
            )

        open_set: List[_Node] = []
        closed_set: Set[Tuple[int, int, int]] = set()
        g_scores: Dict[Tuple[int, int, int], float] = {}

        start_node = _Node(
            x=sx,
            y=sy,
            z=sz,
            h=self._heuristic(sx, sy, sz, gx, gy, gz),
        )
        start_node.f = start_node.h
        heapq.heappush(open_set, start_node)
        g_scores[(sx, sy, sz)] = 0.0

        iterations = 0
        blocked = 0

        while open_set and iterations < max_iterations:
            iterations += 1
            current = heapq.heappop(open_set)
            current_key = (current.x, current.y, current.z)

            if current_key in closed_set:
                continue
            closed_set.add(current_key)

            # Reached goal
            if current.x == gx and current.y == gy and current.z == gz:
                return self._reconstruct_path(current, closed_set)

            # Expand neighbors
            neighbors = self._get_neighbors(current.x, current.y, current.z)
            for nx, ny, nz in neighbors:
                neighbor_key = (nx, ny, nz)
                if neighbor_key in closed_set:
                    continue

                tentative_g = current.g + self._move_cost(
                    current.x,
                    current.y,
                    current.z,
                    nx,
                    ny,
                    nz,
                )

                if tentative_g < g_scores.get(neighbor_key, float("inf")):
                    g_scores[neighbor_key] = tentative_g
                    h = self._heuristic(nx, ny, nz, gx, gy, gz)
                    node = _Node(
                        x=nx,
                        y=ny,
                        z=nz,
                        g=tentative_g,
                        h=h,
                        f=tentative_g + h,
                        parent=current,
                    )
                    heapq.heappush(open_set, node)

        # No path found
        return PathResult(
            waypoints=[],
            distance=0.0,
            steps=0,
            floors_traversed=0,
            reachable=False,
            blocked_tiles=blocked,
        )

    def _get_neighbors(self, x: int, y: int, z: int) -> List[Tuple[int, int, int]]:
        """Get walkable neighboring tiles."""
        neighbors: List[Tuple[int, int, int]] = []

        for dx, dy in self._directions:
            nx, ny, nz = x + dx, y + dy, z
            if self._is_walkable(nx, ny, nz):
                # Check diagonal blocking (can't cut through walls)
                if abs(dx) + abs(dy) == 2:
                    if not self._is_walkable(x + dx, y, z) or not self._is_walkable(
                        x, y + dy, z
                    ):
                        continue
                neighbors.append((nx, ny, nz))

        # Floor transitions (stairs)
        if self._use_stairs:
            for dz in self.Z_STEPS:
                nz = z + dz
                # Stairs exist if there's a walkable tile directly above/below
                if self._is_walkable(x, y, nz):
                    neighbors.append((x, y, nz))

        return neighbors

    def _reconstruct_path(
        self,
        node: _Node,
        closed_set: Set[Tuple[int, int, int]],
    ) -> PathResult:
        """Reconstruct path from goal node back to start."""
        waypoints: List[Tuple[int, int, int]] = []
        floors: Set[int] = set()
        current: Optional[_Node] = node

        while current is not None:
            waypoints.append((current.x, current.y, current.z))
            floors.add(current.z)
            current = current.parent

        waypoints.reverse()
        distance = node.g

        return PathResult(
            waypoints=waypoints,
            distance=distance,
            steps=len(waypoints) - 1,
            floors_traversed=len(floors) - 1,
            reachable=True,
            blocked_tiles=0,
        )

    def find_nearest_spawn(
        self,
        from_pos: Tuple[int, int, int],
        max_range: int = 50,
    ) -> Optional[Tuple[int, int, int]]:
        """Find nearest tile with a monster spawn within range."""
        fx, fy, fz = from_pos
        best_dist = float("inf")
        best_pos = None

        for dx in range(-max_range, max_range + 1):
            for dy in range(-max_range, max_range + 1):
                tx, ty = fx + dx, fy + dy
                if self._has_spawn(tx, ty, fz):
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < best_dist:
                        best_dist = dist
                        best_pos = (tx, ty, fz)

        return best_pos

    def reachable_tiles(
        self,
        start: Tuple[int, int, int],
        max_steps: int = 200,
    ) -> Set[Tuple[int, int, int]]:
        """BFS to find all reachable tiles from a starting position."""
        sx, sy, sz = start
        if not self._is_walkable(sx, sy, sz):
            return set()

        visited: Set[Tuple[int, int, int]] = set()
        queue: List[Tuple[int, int, int, int]] = [(sx, sy, sz, 0)]
        visited.add((sx, sy, sz))

        while queue:
            cx, cy, cz, depth = queue.pop(0)
            if depth >= max_steps:
                continue

            for nx, ny, nz in self._get_neighbors(cx, cy, cz):
                if (nx, ny, nz) not in visited:
                    visited.add((nx, ny, nz))
                    queue.append((nx, ny, nz, depth + 1))

        return visited

    def coverage_ratio(
        self,
        start: Tuple[int, int, int],
        max_steps: int = 200,
    ) -> float:
        """Calculate what fraction of all tiles are reachable from start."""
        reachable = self.reachable_tiles(start, max_steps)

        # Count all walkable tiles in world
        total_walkable = 0
        for key, tile in self._world.tiles.items():
            if tile.ground is not None or tile.items:
                total_walkable += 1

        if total_walkable == 0:
            return 0.0

        return len(reachable) / total_walkable

    def distance_map(
        self,
        start: Tuple[int, int, int],
        max_steps: int = 100,
    ) -> Dict[Tuple[int, int, int], float]:
        """BFS distance map from start to all reachable tiles within max_steps."""
        sx, sy, sz = start
        distances: Dict[Tuple[int, int, int], float] = {}
        if not self._is_walkable(sx, sy, sz):
            return distances

        distances[(sx, sy, sz)] = 0.0
        queue: List[Tuple[int, int, int, float]] = [(sx, sy, sz, 0.0)]

        while queue:
            cx, cy, cz, cd = queue.pop(0)
            if cd >= max_steps:
                continue

            for nx, ny, nz in self._get_neighbors(cx, cy, cz):
                new_dist = cd + self._move_cost(cx, cy, cz, nx, ny, nz)
                if (nx, ny, nz) not in distances or new_dist < distances[(nx, ny, nz)]:
                    distances[(nx, ny, nz)] = new_dist
                    queue.append((nx, ny, nz, new_dist))

        return distances

    def clear_cache(self) -> None:
        """Clear the internal tile cache."""
        self._tile_cache.clear()
