"""
WG-20U Critic Panel - Consumes WG20TE_VALIDATION.json, WG20TE_PATH_CONTINUITY.json.

Displays:
    - Disconnected Roads
    - Invalid Floor Links
    - Invalid Brush Selections
    - Building Access Failures
    - Hunt Reachability Failures
    - Connectivity Warnings
"""

from typing import Any, Dict, List


class CriticPanel:
    """Critic panel for validating WG-20TE data quality."""

    def render(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        """Generate critic panel data from WG-20TE datasets."""
        validation = datasets.get("WG20TE_VALIDATION.json", {})
        path_continuity = datasets.get("WG20TE_PATH_CONTINUITY.json", {})
        floor_graph = datasets.get("WG20TE_FLOOR_GRAPH.json", {})
        stair_conn = datasets.get("WG20TE_STAIR_CONNECTIVITY.json", {})
        brush_audit = datasets.get("WG20TE_SEMANTIC_BRUSH_RESOLUTION_AUDIT.json", {})
        building_access = datasets.get(
            "WG20TE_BUILDING_ACCESS_VALIDATION.json", {}
        )
        hunt_reach = datasets.get("WG20TE_HUNT_REACHABILITY.json", {})

        return {
            "disconnected_roads": self._get_disconnected_roads(path_continuity),
            "invalid_floor_links": self._get_invalid_floor_links(
                floor_graph, stair_conn
            ),
            "invalid_brush_selections": self._get_invalid_brush_selections(
                brush_audit
            ),
            "building_access_failures": self._get_building_access_failures(
                building_access
            ),
            "hunt_reachability_failures": self._get_hunt_reachability_failures(
                hunt_reach
            ),
            "connectivity_warnings": self._get_connectivity_warnings(
                datasets
            ),
            "live_rule41_issues": self._get_live_rule41_issues(datasets),
            "overall_validation": validation.get("validation_status", "UNKNOWN"),
        }

    def _get_disconnected_roads(
        self, path_continuity: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check for disconnected roads."""
        issues = []
        if not path_continuity.get("bridges_connect_regions", True):
            issues.append(
                {
                    "type": "BRIDGES_NOT_CONNECTING",
                    "severity": "ERROR",
                    "message": "Bridges are not connecting regions",
                }
            )
        if not path_continuity.get("water_crossings_valid", True):
            issues.append(
                {
                    "type": "WATER_CROSSING_INVALID",
                    "severity": "ERROR",
                    "message": "Water crossings are invalid",
                }
            )
        if not path_continuity.get("districts_connected", True):
            issues.append(
                {
                    "type": "DISTRICTS_DISCONNECTED",
                    "severity": "ERROR",
                    "message": "Districts are not connected",
                }
            )
        return issues

    def _get_live_rule41_issues(
        self, datasets: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Consume RULE-41 warning/error/connectivity/validation events."""
        events = datasets.get("LIVE_GENERATION_TRACE.jsonl", {}).get("events", [])
        issue_categories = {
            "ERROR_EVENT",
            "WARNING_EVENT",
            "CONNECTIVITY_EVENT",
            "VALIDATION_EVENT",
        }
        issues = []
        for event in events:
            if (
                event.get("category") in issue_categories
                or event.get("severity") in {"WARNING", "ERROR", "CRITICAL"}
            ):
                issues.append(
                    {
                        "type": event.get("category"),
                        "severity": event.get("severity"),
                        "message": event.get("description"),
                        "trace_id": event.get("trace_id"),
                        "event_id": event.get("event_id"),
                        "result": event.get("result"),
                    }
                )
        return issues

    def _get_invalid_floor_links(
        self, floor_graph: Dict[str, Any], stair_conn: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check for invalid floor links."""
        issues = []

        # Check orphan floors
        orphan_floors = stair_conn.get("orphan_floors", [])
        for floor_id in orphan_floors:
            issues.append(
                {
                    "type": "ORPHAN_FLOOR",
                    "severity": "WARNING",
                    "message": f"Floor {floor_id} has no stair connectivity",
                    "floor": floor_id,
                }
            )

        return issues

    def _get_invalid_brush_selections(
        self, brush_audit: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check for invalid brush selections."""
        issues = []
        results = brush_audit.get("results", {})
        collision_details = brush_audit.get("brush_collision_details", {})

        for brush_name, roles in collision_details.items():
            if len(roles) > 1:
                issues.append(
                    {
                        "type": "BRUSH_COLLISION",
                        "severity": "WARNING",
                        "message": f"Brush '{brush_name}' assigned to multiple roles",
                        "brush": brush_name,
                        "roles": roles,
                    }
                )

        # Check for semantic invalid brushes
        for role, data in results.items():
            if not data.get("semantic_valid", True):
                issues.append(
                    {
                        "type": "SEMANTIC_INVALID",
                        "severity": "ERROR",
                        "message": f"Role '{role}' has invalid brush selection",
                        "role": role,
                        "selected_brush": data.get("selected_brush", ""),
                    }
                )

        return issues

    def _get_building_access_failures(
        self, building_access: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check for building access failures."""
        issues = []
        buildings = building_access.get("buildings", {})

        for btype, bdata in buildings.items():
            if not bdata.get("accessible", True):
                issues.append(
                    {
                        "type": "BUILDING_INACCESSIBLE",
                        "severity": "ERROR",
                        "message": f"Building type '{btype}' is not accessible",
                        "building_type": btype,
                        "brushes": bdata.get("brushes", []),
                    }
                )

        return issues

    def _get_hunt_reachability_failures(
        self, hunt_reach: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check for hunt reachability failures."""
        issues = []

        if not hunt_reach.get("hunt_entrance_access", True):
            issues.append(
                {
                    "type": "HUNT_ENTRANCE_BLOCKED",
                    "severity": "ERROR",
                    "message": "Hunt entrance is not accessible",
                }
            )
        if not hunt_reach.get("boss_access", True):
            issues.append(
                {
                    "type": "BOSS_ACCESS_BLOCKED",
                    "severity": "ERROR",
                    "message": "Boss area is not accessible",
                }
            )
        if not hunt_reach.get("quest_access", True):
            issues.append(
                {
                    "type": "QUEST_ACCESS_BLOCKED",
                    "severity": "ERROR",
                    "message": "Quest area is not accessible",
                }
            )

        return issues

    def _get_connectivity_warnings(
        self, datasets: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get general connectivity warnings."""
        issues = []

        # Check ramp connectivity
        ramp_conn = datasets.get("WG20TE_RAMP_CONNECTIVITY.json", {})
        if not ramp_conn.get("valid_origin_floor", True):
            issues.append(
                {
                    "type": "INVALID_RAMP_ORIGIN",
                    "severity": "WARNING",
                    "message": "Invalid ramp origin floor detected",
                }
            )
        if not ramp_conn.get("valid_destination_floor", True):
            issues.append(
                {
                    "type": "INVALID_RAMP_DESTINATION",
                    "severity": "WARNING",
                    "message": "Invalid ramp destination floor detected",
                }
            )
        if not ramp_conn.get("all_paths_reachable", True):
            issues.append(
                {
                    "type": "RAMP_PATHS_UNREACHABLE",
                    "severity": "WARNING",
                    "message": "Not all ramp paths are reachable",
                }
            )

        return issues
