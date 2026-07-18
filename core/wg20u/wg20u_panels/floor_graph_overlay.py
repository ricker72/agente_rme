"""
WG-20U Floor Graph Overlay - Consumes WG20TE_FLOOR_GRAPH.json.

Displays:
    - Floor Nodes
    - Floor Edges
    - Stairs
    - Ramps
    - Bridges
    - Teleports
    - Ladders
    - Rope Spots
"""

from typing import Any, Dict, List


class FloorGraphOverlay:
    """Floor graph overlay panel for visual connectivity display."""

    CONNECTOR_CATEGORIES = {
        "vertical": ["stairs", "ramps", "ladders", "rope_spots"],
        "horizontal": ["bridges"],
        "teleport": ["teleports"],
        "special": ["holes", "teleports"],
    }

    def render(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        """Generate floor graph overlay data from WG-20TE floor graph."""
        floor_graph = datasets.get("WG20TE_FLOOR_GRAPH.json", {})
        stair_conn = datasets.get("WG20TE_STAIR_CONNECTIVITY.json", {})

        edges = floor_graph.get("edges", [])
        connectivity_map = floor_graph.get("floor_connectivity_map", {})

        return {
            "floor_nodes": self._get_floor_nodes(connectivity_map),
            "floor_edges": edges,
            "connector_breakdown": self._get_connector_breakdown(edges),
            "stairs": self._extract_connectors(stair_conn.get("stair_edges", [])),
            "ramps": self._extract_connectors(
                datasets.get("WG20TE_RAMP_CONNECTIVITY.json", {}).get(
                    "ramp_edges", []
                )
            ),
            "bridges": self._extract_connectors(
                datasets.get("WG20TE_BRIDGE_CONNECTIVITY.json", {}).get(
                    "bridge_edges", []
                )
            ),
            "teleports": self._extract_teleports(edges),
            "ladders": self._extract_by_type(edges, "ladders"),
            "rope_spots": self._extract_by_type(edges, "rope_spots"),
            "graph_metrics": self._compute_graph_metrics(
                floor_graph, edges, connectivity_map
            ),
        }

    def _get_floor_nodes(
        self, connectivity_map: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get all floor nodes with their connectivity info."""
        nodes = []
        for floor_id, floor_data in connectivity_map.items():
            nodes.append(
                {
                    "floor": int(floor_id),
                    "connected_floors": floor_data.get("connected_floors", []),
                    "up_access": floor_data.get("has_up_access", False),
                    "down_access": floor_data.get("has_down_access", False),
                }
            )
        return sorted(nodes, key=lambda n: n["floor"])

    def _get_connector_breakdown(
        self, edges: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Count edges by connector type."""
        counts = {ct: 0 for ct in [
            "stairs", "ramps", "bridges", "teleports", "ladders", "rope_spots", "holes"
        ]}

        for edge in edges:
            for connector in edge.get("connectors", []):
                if connector in counts:
                    counts[connector] += 1

        return counts

    def _extract_connectors(
        self, edges: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract connector edges."""
        return [
            {
                "from_floor": e.get("from"),
                "to_floor": e.get("to"),
                "connectors": e.get("connectors", []),
            }
            for e in edges
        ]

    def _extract_teleports(
        self, edges: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract teleport-only edges."""
        teleports = []
        for edge in edges:
            if "teleports" in edge.get("connectors", []):
                teleports.append(
                    {
                        "from_floor": edge.get("from"),
                        "to_floor": edge.get("to"),
                    }
                )
        return teleports

    def _extract_by_type(
        self, edges: List[Dict[str, Any]], connector_type: str
    ) -> List[Dict[str, Any]]:
        """Extract edges containing a specific connector type."""
        extracted = []
        for edge in edges:
            if connector_type in edge.get("connectors", []):
                extracted.append(
                    {
                        "from_floor": edge.get("from"),
                        "to_floor": edge.get("to"),
                    }
                )
        return extracted

    def _compute_graph_metrics(
        self,
        floor_graph: Dict[str, Any],
        edges: List[Dict[str, Any]],
        connectivity_map: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute overall graph metrics."""
        total_floors = floor_graph.get("floor_count", 0)

        floors_with_up = sum(
            1 for f in connectivity_map.values() if f.get("has_up_access", False)
        )
        floors_with_down = sum(
            1 for f in connectivity_map.values() if f.get("has_down_access", False)
        )

        return {
            "total_floors": total_floors,
            "total_edges": len(edges),
            "floors_with_up_access": floors_with_up,
            "floors_with_down_access": floors_with_down,
            "connectivity_ratio": len(edges) / max(total_floors - 1, 1)
            if total_floors > 1
            else 0,
            "is_fully_connected": (
                floors_with_up == total_floors
                and floors_with_down == total_floors
            ),
        }