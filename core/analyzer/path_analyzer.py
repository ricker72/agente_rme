"""
HITO 12 — Path Analyzer: analiza rutas, conectividad y distancias
entre waypoints, spawns y puntos de interés en un mapa.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple


class PathAnalyzer:
    """Analiza conectividad entre waypoints, spawns y houses."""

    def analyze(
        self,
        waypoints: List[Dict[str, object]],
        spawns: List[Dict[str, object]],
    ) -> Dict[str, object]:
        """Analiza rutas y conectividad del mapa.

        Args:
            waypoints: Lista de waypoints [{name, x, y, z}, ...].
            spawns: Lista de spawns [{monster, x, y, z, radius}, ...].

        Returns:
            Dict con análisis de rutas.
        """
        if not waypoints:
            return {
                "total_waypoints": 0,
                "waypoint_distances": [],
                "nearest_waypoint_to_spawns": [],
                "path_graph": {"nodes": [], "edges": []},
                "connectivity_summary": "No waypoints available",
            }

        # Calcular distancias entre waypoints
        wp_distances = self._compute_waypoint_distances(waypoints)

        # Calcular nearest waypoint for each spawn
        nearest = self._nearest_waypoint_for_spawns(waypoints, spawns)

        # Construir grafo de conectividad
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
    # Cálculos de distancia
    # ------------------------------------------------------------------

    @staticmethod
    def _manhattan(a: Dict[str, object], b: Dict[str, object]) -> int:
        """Calcula distancia Manhattan entre dos puntos."""
        return abs(int(a.get("x", 0)) - int(b.get("x", 0))) + abs(
            int(a.get("y", 0)) - int(b.get("y", 0))
        )

    @staticmethod
    def _euclidean(a: Dict[str, object], b: Dict[str, object]) -> float:
        """Calcula distancia euclidiana entre dos puntos."""
        dx = int(a.get("x", 0)) - int(b.get("x", 0))
        dy = int(a.get("y", 0)) - int(b.get("y", 0))
        return math.sqrt(dx * dx + dy * dy)

    @staticmethod
    def _same_floor(a: Dict[str, object], b: Dict[str, object]) -> bool:
        return int(a.get("z", 0)) == int(b.get("z", 0))

    # ------------------------------------------------------------------
    # Distancias entre waypoints
    # ------------------------------------------------------------------

    def _compute_waypoint_distances(
        self, waypoints: List[Dict[str, object]]
    ) -> List[Dict[str, object]]:
        """Calcula matriz de distancias entre todos los waypoints."""
        distances = []
        n = len(waypoints)
        for i in range(n):
            for j in range(i + 1, n):
                d = self._manhattan(waypoints[i], waypoints[j])
                distances.append({
                    "from": waypoints[i].get("name", f"wp_{i}"),
                    "to": waypoints[j].get("name", f"wp_{j}"),
                    "distance": d,
                    "same_floor": self._same_floor(waypoints[i], waypoints[j]),
                })
        distances.sort(key=lambda x: x["distance"])
        return distances

    # ------------------------------------------------------------------
    # Nearest waypoint para spawns
    # ------------------------------------------------------------------

    def _nearest_waypoint_for_spawns(
        self,
        waypoints: List[Dict[str, object]],
        spawns: List[Dict[str, object]],
    ) -> List[Dict[str, object]]:
        """Encuentra el waypoint más cercano para cada spawn."""
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
                results.append({
                    "spawn_monster": sp.get("monster", "unknown"),
                    "spawn_x": sp.get("x", 0),
                    "spawn_y": sp.get("y", 0),
                    "waypoint": best_wp.get("name", ""),
                    "waypoint_x": best_wp.get("x", 0),
                    "waypoint_y": best_wp.get("y", 0),
                    "distance": best_dist,
                })

        # Sort por distancia
        results.sort(key=lambda x: x["distance"])
        return results

    # ------------------------------------------------------------------
    # Grafo de conectividad
    # ------------------------------------------------------------------

    def _build_path_graph(
        self,
        waypoints: List[Dict[str, object]],
        distances: List[Dict[str, object]],
    ) -> Dict[str, object]:
        """Construye grafo de conectividad entre waypoints."""
        nodes = []
        seen = set()
        for wp in waypoints:
            name = wp.get("name", "")
            if name and name not in seen:
                seen.add(name)
                nodes.append({
                    "name": name,
                    "x": wp.get("x", 0),
                    "y": wp.get("y", 0),
                    "z": wp.get("z", 0),
                })

        # Edges: solo conexiones cercanas (top 5 por nodo)
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
                edges.append({
                    "from": d["from"],
                    "to": d["to"],
                    "distance": d["distance"],
                })

        return {"nodes": nodes, "edges": edges}

    # ------------------------------------------------------------------
    # Resúmenes
    # ------------------------------------------------------------------

    @staticmethod
    def _summarize_connectivity(
        waypoints: List[Dict[str, object]],
        distances: List[Dict[str, object]],
    ) -> str:
        """Genera resumen textual de conectividad."""
        if not waypoints:
            return "No waypoints"
        if not distances:
            return f"{len(waypoints)} waypoints, no interconnections"
        avg_dist = sum(d["distance"] for d in distances) / len(distances)
        return (
            f"{len(waypoints)} waypoints, "
            f"{len(distances)} connections, "
            f"avg distance: {avg_dist:.0f}"
        )

    @staticmethod
    def _find_furthest_pair(
        distances: List[Dict[str, object]]
    ) -> Optional[Dict[str, object]]:
        """Encuentra el par de waypoints más distantes."""
        if not distances:
            return None
        furthest = max(distances, key=lambda x: x["distance"])
        return furthest

    @staticmethod
    def _find_closest_pair(
        distances: List[Dict[str, object]]
    ) -> Optional[Dict[str, object]]:
        """Encuentra el par de waypoints más cercanos."""
        if not distances:
            return None
        closest = min(distances, key=lambda x: x["distance"])
        return closest

    # ------------------------------------------------------------------
    # Clustering simple de waypoints
    # ------------------------------------------------------------------

    @staticmethod
    def _cluster_waypoints(
        waypoints: List[Dict[str, object]], max_distance: int = 100
    ) -> List[Dict[str, object]]:
        """Agrupa waypoints cercanos en clusters (simple greedy).

        Args:
            waypoints: Lista de waypoints.
            max_distance: Distancia máxima para agrupar.

        Returns:
            Lista de clusters con sus miembros.
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

            clusters.append({
                "cluster_id": cluster_id,
                "center_x": cx,
                "center_y": cy,
                "size": len(cluster),
                "members": [m.get("name", "?") for m in cluster[:10]],
            })

        return clusters