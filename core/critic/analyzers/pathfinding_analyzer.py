"""
PathfindingAnalyzer — A*, BFS, Dijkstra-based analysis.

Produces the pathfinding_score by:
  - Building a walkable graph of ground tiles (one per z).
  - Computing connectivity from a chosen entry point.
  - Detecting inaccessible zones, broken paths, and bottlenecks.
"""

from __future__ import annotations

import heapq
import logging
import math
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from core.world.world_model import WorldModel

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Algorithms: A*, BFS, Dijkstra
# ---------------------------------------------------------------------------

def bfs(start: Tuple[int, int, int],
        goal: Tuple[int, int, int],
        neighbors_fn: Callable[[Tuple[int, int, int]], List[Tuple[int, int, int]]],
        max_nodes: int = 50000) -> Optional[List[Tuple[int, int, int]]]:
    """Breadth-First Search — uniform cost grid expansion."""
    if start == goal:
        return [start]
    visited: Set[Tuple[int, int, int]] = {start}
    parent: Dict[Tuple[int, int, int], Tuple[int, int, int]] = {}
    q: deque = deque([start])
    nodes = 0
    while q:
        node = q.popleft()
        nodes += 1
        if nodes > max_nodes:
            return None
        for n in neighbors_fn(node):
            if n in visited:
                continue
            visited.add(n)
            parent[n] = node
            if n == goal:
                return _reconstruct(parent, start, goal)
            q.append(n)
    return None


def dijkstra(start: Tuple[int, int, int],
             goal: Tuple[int, int, int],
             neighbors_fn: Callable[[Tuple[int, int, int]], List[Tuple[int, int, int]]],
             cost_fn: Optional[Callable[[Tuple[int, int, int], Tuple[int, int, int]], float]] = None,
             max_nodes: int = 50000) -> Optional[List[Tuple[int, int, int]]]:
    """Dijkstra — weighted shortest path (cost 1 for cardinal, sqrt(2) for diagonal)."""
    if start == goal:
        return [start]
    if cost_fn is None:
        cost_fn = _unit_cost
    dist: Dict[Tuple[int, int, int], float] = {start: 0.0}
    parent: Dict[Tuple[int, int, int], Tuple[int, int, int]] = {}
    pq: List[Tuple[float, Tuple[int, int, int]]] = [(0.0, start)]
    nodes = 0
    while pq:
        d, node = heapq.heappop(pq)
        if d > dist.get(node, float("inf")):
            continue
        if node == goal:
            return _reconstruct(parent, start, goal)
        nodes += 1
        if nodes > max_nodes:
            return None
        for n in neighbors_fn(node):
            nd = d + cost_fn(node, n)
            if nd < dist.get(n, float("inf")):
                dist[n] = nd
                parent[n] = node
                heapq.heappush(pq, (nd, n))
    return None


def astar(start: Tuple[int, int, int],
          goal: Tuple[int, int, int],
          neighbors_fn: Callable[[Tuple[int, int, int]], List[Tuple[int, int, int]]],
          heuristic_fn: Optional[Callable[[Tuple[int, int, int], Tuple[int, int, int]], float]] = None,
          cost_fn: Optional[Callable[[Tuple[int, int, int], Tuple[int, int, int]], float]] = None,
          max_nodes: int = 50000) -> Optional[List[Tuple[int, int, int]]]:
    """A* — best-first search with heuristic."""
    if start == goal:
        return [start]
    if heuristic_fn is None:
        heuristic_fn = _zero_heuristic
    if cost_fn is None:
        cost_fn = _unit_cost
    g: Dict[Tuple[int, int, int], float] = {start: 0.0}
    parent: Dict[Tuple[int, int, int], Tuple[int, int, int]] = {}
    f0 = heuristic_fn(start, goal)
    open_heap: List[Tuple[float, Tuple[int, int, int]]] = [(f0, start)]
    closed: Set[Tuple[int, int, int]] = set()
    nodes = 0
    while open_heap:
        _, node = heapq.heappop(open_heap)
        if node in closed:
            continue
        closed.add(node)
        if node == goal:
            return _reconstruct(parent, start, goal)
        nodes += 1
        if nodes > max_nodes:
            return None
        for n in neighbors_fn(node):
            tentative = g[node] + cost_fn(node, n)
            if tentative < g.get(n, float("inf")):
                g[n] = tentative
                parent[n] = node
                f = tentative + heuristic_fn(n, goal)
                heapq.heappush(open_heap, (f, n))
    return None


def _reconstruct(parent: Dict[Tuple[int, int, int], Tuple[int, int, int]],
                 start: Tuple[int, int, int],
                 goal: Tuple[int, int, int]) -> List[Tuple[int, int, int]]:
    path = [goal]
    cur = goal
    while cur in parent:
        cur = parent[cur]
        path.append(cur)
        if cur == start:
            break
    path.reverse()
    return path


def _unit_cost(_a: Tuple[int, int, int], _b: Tuple[int, int, int]) -> float:
    return 1.0


def _zero_heuristic(_a: Tuple[int, int, int], _b: Tuple[int, int, int]) -> float:
    return 0.0


def manhattan_heuristic(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
    """Admissible Manhattan heuristic."""
    return float(abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2]))


def octile_heuristic(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
    """Admissible octile heuristic (sqrt(2)-based)."""
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    dz = abs(a[2] - b[2])
    return (dx + dy) + (math.sqrt(2) - 2) * min(dx, dy) + dz


def octile_cost(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
    """Cardinal = 1.0, diagonal = sqrt(2), z change = 1.5."""
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    dz = abs(a[2] - b[2])
    if dz > 0:
        return 1.5
    if dx == 1 and dy == 1:
        return math.sqrt(2)
    return 1.0


# ---------------------------------------------------------------------------
# Walkable graph
# ---------------------------------------------------------------------------

@dataclass
class WalkableGraph:
    """A graph of walkable tiles built from a world model."""

    world: WorldModel
    positions: Set[Tuple[int, int, int]] = field(default_factory=set)
    spawn_positions: Set[Tuple[int, int, int]] = field(default_factory=set)
    zone_of: Dict[Tuple[int, int, int], str] = field(default_factory=dict)
    max_z: int = 7
    min_z: int = 0

    def build(self) -> "WalkableGraph":
        self.positions.clear()
        self.spawn_positions.clear()
        self.zone_of.clear()
        max_z = -1_000_000
        min_z = 1_000_000
        for key, tile in self.world.tiles.items():
            if tile.ground is None:
                continue
            pos = (tile.x, tile.y, tile.z)
            self.positions.add(pos)
            if tile.spawn is not None:
                self.spawn_positions.add(pos)
            if tile.zone:
                self.zone_of[pos] = tile.zone
            if tile.z > max_z:
                max_z = tile.z
            if tile.z < min_z:
                min_z = tile.z
        self.max_z = max(7, max_z)
        self.min_z = min(0, min_z if min_z != 1_000_000 else 0)
        return self

    def is_walkable(self, pos: Tuple[int, int, int]) -> bool:
        return pos in self.positions

    def neighbors(self, pos: Tuple[int, int, int],
                  allow_diagonal: bool = False,
                  allow_z_change: bool = True) -> List[Tuple[int, int, int]]:
        x, y, z = pos
        out: List[Tuple[int, int, int]] = []
        deltas_4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        deltas_8 = deltas_4 + [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        deltas = deltas_8 if allow_diagonal else deltas_4
        for dx, dy in deltas:
            n = (x + dx, y + dy, z)
            if n in self.positions:
                out.append(n)
        if allow_z_change:
            for dz in (-1, 1):
                n = (x, y, z + dz)
                if n in self.positions:
                    out.append(n)
        return out

    def neighbors_fn(self, pos: Tuple[int, int, int]) -> List[Tuple[int, int, int]]:
        return self.neighbors(pos)

    def find_entry_point(self) -> Optional[Tuple[int, int, int]]:
        """Pick a sensible entry point: a non-spawn ground tile, prefer the largest region."""
        if not self.positions:
            return None
        for pos in self.positions:
            if pos not in self.spawn_positions:
                return pos
        return next(iter(self.positions))


# ---------------------------------------------------------------------------
# PathfindingAnalyzer — produces pathfinding_score
# ---------------------------------------------------------------------------

class PathfindingAnalyzer:
    """
    Uses A*, BFS, and Dijkstra to analyze the navigability of the world.

    Output:
      - pathfinding_score (0-100)
      - issues: inaccessible zones, broken paths, bottlenecks
      - recommendations
      - metrics: distances, path lengths, etc.
    """

    CATEGORY = "pathfinding"

    def __init__(self, max_search_nodes: int = 20000):
        self.max_search_nodes = max_search_nodes

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, world: WorldModel,
                entry: Optional[Tuple[int, int, int]] = None
                ) -> Dict[str, Any]:
        graph = WalkableGraph(world).build()
        return self._analyze_with_graph(world, graph, entry)

    def analyze_with_graph(self, world: WorldModel,
                           graph: WalkableGraph,
                           entry: Optional[Tuple[int, int, int]] = None
                           ) -> Dict[str, Any]:
        return self._analyze_with_graph(world, graph, entry)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _analyze_with_graph(self, world: WorldModel,
                            graph: WalkableGraph,
                            entry: Optional[Tuple[int, int, int]] = None
                            ) -> Dict[str, Any]:
        from ..models import (
            CriticScore, CriticIssue, CriticRecommendation,
            IssueType, IssueSeverity, RecommendationPriority,
        )

        if not graph.positions:
            return {
                "category": self.CATEGORY,
                "score": CriticScore(self.CATEGORY, 0.0,
                                     notes="World has no walkable tiles"),
                "issues": [
                    CriticIssue(
                        issue_type=IssueType.INACCESSIBLE_ZONE,
                        severity=IssueSeverity.CRITICAL,
                        category=self.CATEGORY,
                        message="No walkable tiles in world",
                    ),
                ],
                "recommendations": [
                    CriticRecommendation(
                        title="Generate ground tiles",
                        description="The world has no walkable ground. Add ground tiles before analyzing.",
                        category=self.CATEGORY,
                        priority=RecommendationPriority.CRITICAL,
                    ),
                ],
                "metrics": {"walkable_tiles": 0, "regions": 0},
            }

        entry = entry or graph.find_entry_point()
        assert entry is not None

        reachable = self._bfs_visit(graph, entry)
        unreachable = graph.positions - reachable
        reach_ratio = len(reachable) / max(len(graph.positions), 1)

        distances = self._dijkstra_distances(graph, entry)
        far_target = self._pick_far_target(graph, distances)
        astar_path: Optional[List[Tuple[int, int, int]]] = None
        astar_len = 0
        if far_target is not None and far_target != entry:
            astar_path = astar(
                entry, far_target, graph.neighbors_fn,
                heuristic_fn=octile_heuristic,
                cost_fn=octile_cost,
                max_nodes=self.max_search_nodes,
            )
            astar_len = len(astar_path) if astar_path else 0

        bottlenecks = self._detect_bottlenecks(graph, reachable)

        # Composite score: 70 baseline + 25 reachability + 5 bottleneck health
        bn_score = max(0.0, 1.0 - (len(bottlenecks) / max(len(reachable), 1)) * 25.0)
        score_value = (
            70.0
            + reach_ratio * 100.0 * 0.25
            + bn_score * 5.0
        )
        score_value = max(0.0, min(100.0, score_value))

        score = CriticScore(
            category=self.CATEGORY,
            value=score_value,
            breakdown={
                "reachability": round(reach_ratio * 100.0, 2),
                "bottleneck_health": round(bn_score * 100.0, 2),
                "astar_path_length": float(astar_len),
            },
            notes=f"Entry point: {entry}, reachable: {len(reachable)}/{len(graph.positions)}",
        )

        issues: List = []
        recs: List = []

        if reach_ratio < 0.5 and len(graph.positions) > 10:
            issues.append(CriticIssue(
                issue_type=IssueType.ISOLATED_REGION,
                severity=IssueSeverity.CRITICAL,
                category=self.CATEGORY,
                message=f"Only {reach_ratio*100:.0f}% of tiles are reachable from entry point",
                details={"reach_ratio": reach_ratio, "unreachable_count": len(unreachable)},
            ))
            recs.append(CriticRecommendation(
                title="Connect isolated regions",
                description="Several map regions are unreachable. Add paths, doors or teleporters to connect them.",
                category=self.CATEGORY,
                priority=RecommendationPriority.CRITICAL,
                action={"connect_to": [list(p) for p in list(unreachable)[:3]]},
            ))
        elif len(unreachable) > 0 and reach_ratio < 0.9 and len(graph.positions) > 10:
            issues.append(CriticIssue(
                issue_type=IssueType.ISOLATED_REGION,
                severity=IssueSeverity.WARNING,
                category=self.CATEGORY,
                message=f"{len(unreachable)} tiles are unreachable from entry point",
                details={"unreachable_count": len(unreachable)},
            ))

        if bottlenecks:
            for tile in bottlenecks[:3]:
                issues.append(CriticIssue(
                    issue_type=IssueType.BOTTLENECK,
                    severity=IssueSeverity.WARNING,
                    category=self.CATEGORY,
                    location=f"({tile[0]},{tile[1]},{tile[2]})",
                    message="Navigation bottleneck detected — routes funnel through this tile",
                ))
            recs.append(CriticRecommendation(
                title="Reduce navigation bottlenecks",
                description="Add secondary routes around bottleneck tiles to improve movement.",
                category=self.CATEGORY,
                priority=RecommendationPriority.MEDIUM,
            ))

        if astar_path is None and far_target is not None and far_target != entry:
            issues.append(CriticIssue(
                issue_type=IssueType.BROKEN_PATH,
                severity=IssueSeverity.CRITICAL,
                category=self.CATEGORY,
                message=f"No path found from entry {entry} to target {far_target}",
            ))

        return {
            "category": self.CATEGORY,
            "score": score,
            "issues": issues,
            "recommendations": recs,
            "metrics": {
                "walkable_tiles": len(graph.positions),
                "reachable_tiles": len(reachable),
                "reach_ratio": round(reach_ratio, 4),
                "astar_path_length": astar_len,
                "bottleneck_count": len(bottlenecks),
                "entry_point": list(entry),
                "max_distance": round(max(distances.values()) if distances else 0.0, 2),
            },
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _bfs_visit(self, graph: WalkableGraph,
                   start: Tuple[int, int, int]) -> Set[Tuple[int, int, int]]:
        visited: Set[Tuple[int, int, int]] = {start}
        q: deque = deque([start])
        nodes = 0
        while q:
            cur = q.popleft()
            nodes += 1
            if nodes > self.max_search_nodes:
                break
            for n in graph.neighbors(cur):
                if n in visited:
                    continue
                visited.add(n)
                q.append(n)
        return visited

    def _dijkstra_distances(self, graph: WalkableGraph,
                            start: Tuple[int, int, int]
                            ) -> Dict[Tuple[int, int, int], float]:
        dist: Dict[Tuple[int, int, int], float] = {start: 0.0}
        pq: List[Tuple[float, Tuple[int, int, int]]] = [(0.0, start)]
        nodes = 0
        while pq:
            d, node = heapq.heappop(pq)
            if d > dist.get(node, float("inf")):
                continue
            nodes += 1
            if nodes > self.max_search_nodes:
                break
            for n in graph.neighbors(node):
                nd = d + octile_cost(node, n)
                if nd < dist.get(n, float("inf")):
                    dist[n] = nd
                    heapq.heappush(pq, (nd, n))
        return dist

    def _pick_far_target(self, graph: WalkableGraph,
                         distances: Dict[Tuple[int, int, int], float]
                         ) -> Optional[Tuple[int, int, int]]:
        if not distances:
            return None
        return max(distances.items(), key=lambda kv: kv[1])[0]

    def _detect_bottlenecks(self, graph: WalkableGraph,
                            reachable: Set[Tuple[int, int, int]]
                            ) -> List[Tuple[int, int, int]]:
        bottlenecks: List[Tuple[int, int, int]] = []
        if len(reachable) > 2000:
            sample = list(reachable)[:200]
        else:
            sample = list(reachable)
        for pos in sample:
            degree = sum(1 for _ in graph.neighbors(pos))
            if degree <= 1 and len(reachable) > 1:
                bottlenecks.append(pos)
            elif degree == 2 and len(reachable) > 50:
                bottlenecks.append(pos)
        return bottlenecks[:5]
