"""
WG-20U Connectivity Panel - Consumes WG20TE_FLOOR_GRAPH.json,
WG20TE_STAIR_CONNECTIVITY.json, WG20TE_RAMP_CONNECTIVITY.json.

Displays:
    - floor nodes
    - floor edges
    - connector types
    - orphan connectors
    - accessibility status
"""

from typing import Any, Dict, List


class ConnectivityPanel:
    """Connectivity panel consuming WG-20TE datasets."""

    def render(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        """Generate connectivity panel data from WG-20TE datasets."""
        floor_graph = datasets.get("WG20TE_FLOOR_GRAPH.json", {})
        stair_conn = datasets.get("WG20TE_STAIR_CONNECTIVITY.json", {})
        ramp_conn = datasets.get("WG20TE_RAMP_CONNECTIVITY.json", {})

        return {
            "floor_nodes": self._extract_floor_nodes(floor_graph),
            "floor_edges": floor_graph.get("edges", []),
            "connector_types": floor_graph.get("connector_types_supported", []),
            "orphan_connectors": self._find_orphan_connectors(
                floor_graph, stair_conn, ramp_conn
            ),
            "accessibility_status": self._compute_accessibility_status(
                floor_graph, stair_conn, ramp_conn
            ),
        }

    def _extract_floor_nodes(self, floor_graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract floor node information with connectivity data."""
        nodes = []
        connectivity_map = floor_graph.get("floor_connectivity_map", {})
        for floor_id, floor_data in connectivity_map.items():
            nodes.append(
                {
                    "floor": int(floor_id),
                    "connected_floors": floor_data.get("connected_floors", []),
                    "has_up_access": floor_data.get("has_up_access", False),
                    "has_down_access": floor_data.get("has_down_access", False),
                }
            )
        return nodes

    def _find_orphan_connectors(
        self,
        floor_graph: Dict[str, Any],
        stair_conn: Dict[str, Any],
        ramp_conn: Dict[str, Any],
    ) -> Dict[str, List[int]]:
        """Find orphan connectors (floors with no stairs/ramps)."""
        orphan_floors = set(stair_conn.get("orphan_floors", []))

        return {
            "orphan_floors": list(orphan_floors),
            "orphan_reason": "No stair/ramp connectivity",
        }

    def _compute_accessibility_status(
        self,
        floor_graph: Dict[str, Any],
        stair_conn: Dict[str, Any],
        ramp_conn: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute overall accessibility status from datasets."""
        has_up = all(
            n.get("has_up_access", False)
            for n in floor_graph.get("floor_connectivity_map", {}).values()
        )
        has_down = all(
            n.get("has_down_access", False)
            for n in floor_graph.get("floor_connectivity_map", {}).values()
        )

        return {
            "stair_connectivity_valid": stair_conn.get("valid", False),
            "ramp_connectivity_valid": ramp_conn.get("valid", False),
            "full_up_access": has_up,
            "full_down_access": has_down,
        }