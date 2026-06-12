"""
HITO 12 — Path Analyzer: analyzes routes, connectivity and distances
between waypoints, spawns and points of interest on a map.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Dict, List, Optional


class PathAnalyzer:
    """Analyzes connectivity between waypoints, spawns and houses."""

    def analyze(
        self,
        waypoints: List[Dict[str, object]],
        spawns: List[Dict[str, object]],
    ) -> Dict[str, object]:
        """Analyze routes and map connectivity.

        Args:
            waypoints: List of waypoints [{name, x, y, z}, ...].
            spawns: List of spawns [{monster, x, y, z, radius}, ...].

        Returns:
            Dict with route analysis.
        """
        if not waypoints:
            return {
                "total_waypoints": 0,
                "waypoint_distances": [],
                "nearest_waypoint_to_spawns": [],
                "path_graph": {"nodes": [], "edges": []},
                "connectivity_summary": "No waypoints available",
            }

        # Calculate distances between waypoints
        wp_distances = self._compute_waypoint_distances(waypoints)

        # Calcular nearest waypoint for each spawn
        nearest = self._nearest_waypoint_for_spawns(waypoints, spawns)

        # Build connectivity graph
        graph = self._build_path_graph(waypoints, wp_distances)

        return {
            "total_waypoints": len(waypoints),
            "waypoint_distances": wp_distances[:50],  # limit for large datasets
            "nearest_waypoint_to_spawns": nearest[:50],
            "path_graph": graph,
            "connectivity_summary": self._summarize_connectivity(
                waypoints, wp_distances
            ),
            "furthest_waypoints": self._find_furthest_pair(wp_distances),
            "closest_waypoints": self._find_closest_pair(wp_distances),
            "clustering": self._cluster_waypoints(waypoints),
        }

    # ------------------------------------------------------------------
    # Distance calculations
    # ------------------------------------------------------------------

    @staticmethod
    def _manhattan(a: Dict[str, object], b: Dict[str, object]) -> int:
        """Calculate Manhattan distance between two points."""
        return abs(int(a.get("x", 0)) - int(b.get("x", 0))) + abs(
            int(a.get("y", 0)) - int(b.get("y", 0))
        )

    @staticmethod
    def _euclidean(a: Dict[str, object], b: Dict[str, object]) -> float:
        """Calculate Euclidean distance between two points."""
        dx = int(a.get("x", 0)) - int(b.get("x", 0))
        dy = int(a.get("y", 0)) - int(b.get("y", 0))
        return math.sqrt(dx * dx + dy * dy)

    @staticmethod
    def _same_floor(a: Dict[str, object], b: Dict[str, object]) -> bool:
        return int(a.get("z", 0)) == int(b.get("z", 0))

    # ------------------------------------------------------------------
    # Waypoint distances
    # ------------------------------------------------------------------

    def _compute_waypoint_distances(
        self, waypoints: List[Dict[str, object]]
    ) -> List[Dict[str, object]]:
        """Calculate distance matrix between all waypoints."""
        distances = []
        n = len(waypoints)
        for i in range(n):
            for j in range(i + 1, n):
                d = self._manhattan(waypoints[i], waypoints[j])
                distances.append(
                    {
                        "from": waypoints[i].get("name", f"wp_{i}"),
                        "to": waypoints[j].get("name", f"wp_{j}"),
                        "distance": d,
                        "same_floor": self._same_floor(waypoints[i], waypoints[j]),
                    }
                )
        distances.sort(key=lambda x: x["distance"])
        return distances

    # ------------------------------------------------------------------
    # Nearest waypoint for spawns
    # ------------------------------------------------------------------

    def _nearest_waypoint_for_spawns(
        self,
        waypoints: List[Dict[str, object]],
        spawns: List[Dict[str, object]],
    ) -> List[Dict[str, object]]:
        """Find the nearest waypoint for each spawn."""
        if not spawns or not waypoints:
            return []

        results = []
        for sp in spawns:
            best_wp = None
            best_dist = float("inf")
            for wp in waypoints:
                d = self._manhattan(sp, wp)
                if d < best_dist:
                    best_dist = d
                    best_wp = wp
            if best_wp:
                results.append(
                    {
                        "spawn_monster": sp.get("monster", "unknown"),
                        "spawn_x": sp.get("x", 0),
                        "spawn_y": sp.get("y", 0),
                        "waypoint": best_wp.get("name", ""),
                        "waypoint_x": best_wp.get("x", 0),
                        "waypoint_y": best_wp.get("y", 0),
                        "distance": best_dist,
                    }
                )

        # Sort by distance
        results.sort(key=lambda x: x["distance"])
        return results

    # ------------------------------------------------------------------
    # Connectivity graph
    # ------------------------------------------------------------------

    def _build_path_graph(
        self,
        waypoints: List[Dict[str, object]],
        distances: List[Dict[str, object]],
    ) -> Dict[str, object]:
        """Build connectivity graph between waypoints."""
        nodes = []
        seen = set()
        for wp in waypoints:
            name = wp.get("name", "")
            if name and name not in seen:
                seen.add(name)
                nodes.append(
                    {
                        "name": name,
                        "x": wp.get("x", 0),
                        "y": wp.get("y", 0),
                        "z": wp.get("z", 0),
                    }
                )

        # Edges: only close connections (top 5 per node)
        edges = []
        adjacency = defaultdict(list)
        for d in distances:
            adjacency[d["from"]].append(d)
            adjacency[d["to"]].append(d)

        edge_seen = set()
        for d in distances[:200]:  # limit total edges
            key = tuple(sorted([str(d["from"]), str(d["to"])]))
            if key not in edge_seen:
                edge_seen.add(key)
                edges.append(
                    {
                        "from": d["from"],
                        "to": d["to"],
                        "distance": d["distance"],
                    }
                )

        return {"nodes": nodes, "edges": edges}

    # ------------------------------------------------------------------
    # Summaries
    # ------------------------------------------------------------------

    @staticmethod
    def _summarize_connectivity(
        waypoints: List[Dict[str, object]],
        distances: List[Dict[str, object]],
    ) -> str:
        """Generate textual connectivity summary."""
        if not waypoints:
            return "No waypoints"
        if not distances:
            return f"{len(waypoints)} waypoints, no interconnections"
        avg_dist = sum(d["distance"] for d in distances) / len(distances)
        return f"{len(waypoints)} waypoints, {len(distances)} connections, avg distance: {avg_dist:.0f}"

    @staticmethod
    def _find_furthest_pair(
        distances: List[Dict[str, object]],
    ) -> Optional[Dict[str, object]]:
        """Find the furthest pair of waypoints."""
        if not distances:
            return None
        furthest = max(distances, key=lambda x: x["distance"])
        return furthest

    @staticmethod
    def _find_closest_pair(
        distances: List[Dict[str, object]],
    ) -> Optional[Dict[str, object]]:
        """Find the closest pair of waypoints."""
        if not distances:
            return None
        closest = min(distances, key=lambda x: x["distance"])
        return closest

    # ------------------------------------------------------------------
    # Simple waypoint clustering
    # ------------------------------------------------------------------

    @staticmethod
    def _cluster_waypoints(
        waypoints: List[Dict[str, object]], max_distance: int = 100
    ) -> List[Dict[str, object]]:
        """Cluster nearby waypoints (simple greedy).

        Args:
            waypoints: List of waypoints.
            max_distance: Maximum distance for grouping.

        Returns:
            List of clusters with their members.
        """
        if not waypoints:
            return []

        remaining = list(waypoints)
        clusters = []
        cluster_id = 0

        while remaining:
            seed = remaining.pop(0)
            cluster = [seed]
            members_left = list(remaining)
            remaining = []

            for wp in members_left:
                dx = abs(int(wp.get("x", 0)) - int(seed.get("x", 0)))
                dy = abs(int(wp.get("y", 0)) - int(seed.get("y", 0)))
                if dx <= max_distance and dy <= max_distance:
                    cluster.append(wp)
                else:
                    remaining.append(wp)

            cluster_id += 1
            cx = sum(int(m.get("x", 0)) for m in cluster) // len(cluster)
            cy = sum(int(m.get("y", 0)) for m in cluster) // len(cluster)

            clusters.append(
                {
                    "cluster_id": cluster_id,
                    "center_x": cx,
                    "center_y": cy,
                    "size": len(cluster),
                    "members": [m.get("name", "?") for m in cluster[:10]],
                }
            )

        return clusters
