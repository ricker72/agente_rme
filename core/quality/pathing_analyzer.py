from __future__ import annotations

from collections import deque
from typing import Any, Dict, List, Set, Tuple


class PathingAnalyzer:
    def analyze(self, world_model: Any) -> Dict[str, object]:
        traversable = self._build_traversable_set(world_model)
        if not traversable:
            return {
                "dead_ends": [],
                "soft_locks": [],
                "hard_locks": [],
                "unreachable_zones": [],
                "warnings": ["The map contains no traversable tiles."],
            }

        adjacency = self._build_adjacency(traversable)
        dead_ends = [
            coords for coords, neighbors in adjacency.items() if len(neighbors) == 1
        ]
        isolated = [
            coords for coords, neighbors in adjacency.items() if len(neighbors) == 0
        ]
        soft_locks = []
        hard_locks = []
        unreachable = self._find_unreachable_zones(world_model, traversable)

        for coords in dead_ends:
            tile = self._tile_at(world_model, coords)
            if tile and getattr(tile, "spawn", None):
                soft_locks.append({"x": coords[0], "y": coords[1], "z": coords[2]})
            elif tile and getattr(tile, "creature", None):
                soft_locks.append({"x": coords[0], "y": coords[1], "z": coords[2]})

        for coords in isolated:
            hard_locks.append({"x": coords[0], "y": coords[1], "z": coords[2]})

        warnings = []
        if dead_ends:
            warnings.append(f"Found {len(dead_ends)} dead ends.")
        if unreachable:
            warnings.append(f"Found {len(unreachable)} unreachable zones.")
        if hard_locks:
            warnings.append(f"Found {len(hard_locks)} hard locks.")

        return {
            "dead_ends": dead_ends,
            "soft_locks": soft_locks,
            "hard_locks": hard_locks,
            "unreachable_zones": unreachable,
            "warnings": warnings,
        }

    def _build_traversable_set(self, world_model: Any) -> Set[Tuple[int, int, int]]:
        traversable = set()
        for tile in getattr(world_model, "tiles", {}).values():
            ground = getattr(tile, "ground", "") or ""
            if "wall" not in ground.lower() and "void" not in ground.lower():
                traversable.add((tile.x, tile.y, tile.z))
        return traversable

    def _build_adjacency(
        self, traversable: Set[Tuple[int, int, int]]
    ) -> Dict[Tuple[int, int, int], List[Tuple[int, int, int]]]:
        adjacency = {}
        for x, y, z in traversable:
            neighbors = []
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                candidate = (x + dx, y + dy, z)
                if candidate in traversable:
                    neighbors.append(candidate)
            adjacency[(x, y, z)] = neighbors
        return adjacency

    def _find_unreachable_zones(
        self, world_model: Any, traversable: Set[Tuple[int, int, int]]
    ) -> List[Dict[str, int]]:
        if not traversable:
            return []
        visited = set()
        start = next(iter(traversable))
        queue = deque([start])
        visited.add(start)

        while queue:
            current = queue.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbour = (current[0] + dx, current[1] + dy, current[2])
                if neighbour in traversable and neighbour not in visited:
                    visited.add(neighbour)
                    queue.append(neighbour)

        return [
            {"x": x, "y": y, "z": z}
            for x, y, z in traversable
            if (x, y, z) not in visited
        ]

    def _tile_at(self, world_model: Any, coords: Tuple[int, int, int]) -> Any:
        return getattr(world_model, "tiles", {}).get(
            f"{coords[0]}:{coords[1]}:{coords[2]}"
        )

    def _find_reachable_tiles(self, world_model: Any) -> List[Tuple[int, int, int]]:
        traversable = self._build_traversable_set(world_model)
        if not traversable:
            return []
        visited = set()
        start = next(iter(traversable))
        queue = deque([start])
        visited.add(start)
        while queue:
            current = queue.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbour = (current[0] + dx, current[1] + dy, current[2])
                if neighbour in traversable and neighbour not in visited:
                    visited.add(neighbour)
                    queue.append(neighbour)
        return list(visited)
