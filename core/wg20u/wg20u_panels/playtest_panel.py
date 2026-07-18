"""
WG-20U Playtest Panel - Consumes WG20TE_BUILDING_ACCESS_VALIDATION.json,
WG20TE_HUNT_REACHABILITY.json, WG20TE_FLOOR_GRAPH.json.

Displays:
    - Accessible Buildings
    - Reachable Hunts
    - Reachable Floors
    - Traversal Status
    - Navigation Validation
"""

from typing import Any, Dict


class PlaytestPanel:
    """Playtest panel for navigation validation using WG-20TE datasets."""

    def render(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        """Generate playtest panel data from WG-20TE datasets."""
        building_access = datasets.get(
            "WG20TE_BUILDING_ACCESS_VALIDATION.json", {}
        )
        hunt_reach = datasets.get("WG20TE_HUNT_REACHABILITY.json", {})
        floor_graph = datasets.get("WG20TE_FLOOR_GRAPH.json", {})
        stair_conn = datasets.get("WG20TE_STAIR_CONNECTIVITY.json", {})

        return {
            "accessible_buildings": self._get_accessible_buildings(building_access),
            "reachable_hunts": self._get_reachable_hunts(hunt_reach),
            "reachable_floors": self._get_reachable_floors(stair_conn),
            "traversal_status": self._get_traversal_status(
                floor_graph, stair_conn
            ),
            "navigation_validation": self._get_navigation_validation(
                datasets
            ),
        }

    def _get_accessible_buildings(
        self, building_access: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get accessible building information."""
        buildings = building_access.get("buildings", {})

        accessible = []
        inaccessible = []

        for btype, bdata in buildings.items():
            entry = {
                "type": btype,
                "brush_count": bdata.get("brush_count", 0),
                "brushes": bdata.get("brushes", []),
            }
            if bdata.get("accessible", False):
                accessible.append(entry)
            else:
                inaccessible.append(entry)

        return {
            "total_types": len(buildings),
            "accessible_count": len(accessible),
            "accessible_buildings": accessible,
            "inaccessible_buildings": inaccessible,
        }

    def _get_reachable_hunts(
        self, hunt_reach: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get reachable hunts information."""
        return {
            "hunt_brushes_found": hunt_reach.get("hunt_brushes_found", 0),
            "boss_brushes_found": hunt_reach.get("boss_brushes_found", 0),
            "quest_brushes_found": hunt_reach.get("quest_brushes_found", 0),
            "hunt_samples": hunt_reach.get("hunt_brush_samples", []),
            "boss_samples": hunt_reach.get("boss_brush_samples", []),
            "quest_samples": hunt_reach.get("quest_brush_samples", []),
            "hunt_entrance_access": hunt_reach.get("hunt_entrance_access", False),
            "boss_access": hunt_reach.get("boss_access", False),
            "quest_access": hunt_reach.get("quest_access", False),
        }

    def _get_reachable_floors(
        self, stair_conn: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get reachable floor information."""
        reachable = stair_conn.get("reachable_destinations", {})
        orphan_floors = stair_conn.get("orphan_floors", [])

        reachable_from_all = True
        for floor_id, targets in reachable.items():
            if len(targets) == 0:
                reachable_from_all = False
                break

        return {
            "reachable_from_floor_0": reachable.get("0", []),
            "orphan_floors": orphan_floors,
            "all_floors_reachable": reachable_from_all,
            "floor_count": len(reachable),
            "total_reachable_destinations": sum(len(v) for v in reachable.values()),
        }

    def _get_traversal_status(
        self, floor_graph: Dict[str, Any], stair_conn: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get traversal status between floors."""
        edges = floor_graph.get("edges", [])
        connectivity_map = floor_graph.get("floor_connectivity_map", {})

        up_traversable = []
        down_traversable = []

        for floor_id, floor_data in connectivity_map.items():
            if floor_data.get("has_up_access", False):
                up_traversable.append(int(floor_id))
            if floor_data.get("has_down_access", False):
                down_traversable.append(int(floor_id))

        return {
            "total_edges": len(edges),
            "floors_with_up_access": up_traversable,
            "floors_with_down_access": down_traversable,
            "can_traverse_up": len(up_traversable) == floor_graph.get("floor_count", 0),
            "can_traverse_down": len(down_traversable) == floor_graph.get("floor_count", 0),
        }

    def _get_navigation_validation(
        self, datasets: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get overall navigation validation status."""
        validation = datasets.get("WG20TE_VALIDATION.json", {})
        path_continuity = datasets.get("WG20TE_PATH_CONTINUITY.json", {})

        checks = validation.get("checks", {})

        return {
            "status": validation.get("validation_status", "UNKNOWN"),
            "all_checks_passed": validation.get("all_passed", False),
            "floor_graph_valid": checks.get("floor_graph_valid", False),
            "stair_connectivity_valid": checks.get("stair_connectivity_valid", False),
            "ramp_connectivity_valid": checks.get("ramp_connectivity_valid", False),
            "building_access_valid": checks.get("building_access_valid", False),
            "hunt_reachability_valid": checks.get("hunt_reachability_valid", False),
            "path_continuity_valid": checks.get("path_continuity_valid", False),
            "districts_connected": path_continuity.get("districts_connected", False),
            "all_floors_reachable_from_ground": path_continuity.get(
                "all_floors_reachable_from_ground", False
            ),
        }
