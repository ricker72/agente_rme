"""
WG-20U Viewport - Visualizes floor graph, stair links, ramp links,
building accessibility, hunt reachability, path continuity, brush resolution.
"""

from typing import Any, Dict


class Wg20uViewport:
    """
    Visualizes connectivity intelligence from WG-20TE datasets.

    Displays:
    - Floor Graph
    - Stair Links
    - Ramp Links
    - Building Accessibility
    - Hunt Accessibility
    - Path Continuity
    - Brush Resolution
    - Role Resolution
    """

    CONNECTOR_TYPE_NAMES = {
        "stairs": "STAIRS",
        "ramps": "RAMPS",
        "teleports": "TELEPORTS",
        "bridges": "BRIDGES",
        "holes": "HOLES",
        "ladders": "LADDERS",
        "rope_spots": "ROPE_SPOTS",
    }

    def render(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        """Generate viewport visualization data from all datasets."""
        return {
            "floor_graph": self._get_floor_graph(datasets),
            "stair_links": self._get_stair_links(datasets),
            "ramp_links": self._get_ramp_links(datasets),
            "building_accessibility": self._get_building_accessibility(datasets),
            "hunt_accessibility": self._get_hunt_accessibility(datasets),
            "path_continuity": self._get_path_continuity(datasets),
            "brush_resolution": self._get_brush_resolution(datasets),
            "role_resolution": self._get_role_resolution(datasets),
            "live_generation_trace_panel": self._get_live_generation_trace_panel(
                datasets
            ),
        }

    def _get_floor_graph(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        """Extract floor graph visualization data."""
        floor_graph = datasets.get("WG20TE_FLOOR_GRAPH.json", {})
        return {
            "floor_count": floor_graph.get("floor_count", 0),
            "floors": floor_graph.get("floors", []),
            "connector_types_supported": floor_graph.get(
                "connector_types_supported", []
            ),
            "edges": floor_graph.get("edges", []),
            "floor_connectivity_map": floor_graph.get("floor_connectivity_map", {}),
        }

    def _get_stair_links(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        """Extract stair connectivity visualization data."""
        stair_data = datasets.get("WG20TE_STAIR_CONNECTIVITY.json", {})
        return {
            "floors_analyzed": stair_data.get("floors_analyzed", []),
            "stair_edges": stair_data.get("stair_edges", []),
            "up_links": stair_data.get("up_links", []),
            "down_links": stair_data.get("down_links", []),
            "bidirectional_edges": stair_data.get("bidirectional_edges", []),
            "orphan_floors": stair_data.get("orphan_floors", []),
            "valid": stair_data.get("valid", False),
        }

    def _get_ramp_links(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        """Extract ramp connectivity visualization data."""
        ramp_data = datasets.get("WG20TE_RAMP_CONNECTIVITY.json", {})
        return {
            "ramp_edges": ramp_data.get("ramp_edges", []),
            "up_ramps": ramp_data.get("up_ramps", []),
            "down_ramps": ramp_data.get("down_ramps", []),
            "valid_origin_floor": ramp_data.get("valid_origin_floor", False),
            "valid_destination_floor": ramp_data.get("valid_destination_floor", False),
            "all_paths_reachable": ramp_data.get("all_paths_reachable", False),
        }

    def _get_building_accessibility(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        """Extract building accessibility visualization data."""
        building_data = datasets.get(
            "WG20TE_BUILDING_ACCESS_VALIDATION.json", {}
        )
        return {
            "building_types_analyzed": building_data.get(
                "building_types_analyzed", []
            ),
            "buildings": building_data.get("buildings", {}),
            "total_building_brushes": building_data.get("total_building_brushes", 0),
            "all_types_have_brushes": building_data.get("all_types_have_brushes", False),
            "all_floors_have_connectivity": building_data.get(
                "all_floors_have_connectivity", False
            ),
        }

    def _get_hunt_accessibility(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        """Extract hunt reachability visualization data."""
        hunt_data = datasets.get("WG20TE_HUNT_REACHABILITY.json", {})
        return {
            "hunt_brushes_found": hunt_data.get("hunt_brushes_found", 0),
            "boss_brushes_found": hunt_data.get("boss_brushes_found", 0),
            "quest_brushes_found": hunt_data.get("quest_brushes_found", 0),
            "floor_reachability": hunt_data.get("floor_reachability", {}),
            "hunt_entrance_access": hunt_data.get("hunt_entrance_access", False),
            "boss_access": hunt_data.get("boss_access", False),
            "quest_access": hunt_data.get("quest_access", False),
        }

    def _get_path_continuity(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        """Extract path continuity visualization data."""
        path_data = datasets.get("WG20TE_PATH_CONTINUITY.json", {})
        return {
            "road_edges_total": path_data.get("road_edges_total", 0),
            "road_brush_count": path_data.get("road_brush_count", 0),
            "water_brush_count": path_data.get("water_brush_count", 0),
            "bridges_connect_regions": path_data.get("bridges_connect_regions", False),
            "water_crossings_valid": path_data.get("water_crossings_valid", False),
            "districts_connected": path_data.get("districts_connected", False),
            "all_floors_reachable_from_ground": path_data.get(
                "all_floors_reachable_from_ground", False
            ),
            "isolated_districts": path_data.get("isolated_districts", []),
        }

    def _get_brush_resolution(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        """Extract semantic brush resolution visualization data."""
        brush_data = datasets.get(
            "WG20TE_SEMANTIC_BRUSH_RESOLUTION_AUDIT.json", {}
        )
        return {
            "roles_audited": brush_data.get("roles_audited", []),
            "results": brush_data.get("results", {}),
            "brush_collision_counts": brush_data.get("brush_collision_counts", {}),
            "semantic_collision_ratio": brush_data.get("semantic_collision_ratio", 0),
            "semantic_brush_audit_passed": brush_data.get(
                "semantic_brush_audit_passed", False
            ),
        }

    def _get_role_resolution(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        """Extract role uniqueness visualization data."""
        role_data = datasets.get("WG20TE_ROLE_UNIQUENESS_AUDIT.json", {})
        return {
            "total_roles_audited": role_data.get("total_roles_audited", 0),
            "unique_brushes_used": role_data.get("unique_brushes_used", 0),
            "brush_collisions": role_data.get("brush_collisions", {}),
            "collision_count": role_data.get("collision_count", 0),
            "worst_collision_brush": role_data.get("worst_collision_brush", ""),
            "role_uniqueness_passed": role_data.get("role_uniqueness_passed", False),
        }

    def _get_live_generation_trace_panel(
        self, datasets: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Expose RULE-41 trace events without synthesizing new events."""
        trace_data = datasets.get("LIVE_GENERATION_TRACE.jsonl", {})
        event_stream = datasets.get("EVENT_STREAM.json", {})
        timeline = datasets.get("GENERATION_TIMELINE.json", {})
        audit = datasets.get("OBSERVABILITY_AUDIT.json", {})
        events = trace_data.get("events") or event_stream.get("events", [])
        active_messages = [
            event.get("description", "")
            for event in events[-25:]
            if event.get("description")
        ]
        return {
            "consumer_only": True,
            "synthetic_events_created": False,
            "events": events,
            "timeline": timeline.get("events", []),
            "active_messages": active_messages,
            "observability_status": audit.get("status", "NO_TRACE_ARTIFACTS"),
            "trace_count": audit.get("trace_count", 0),
            "events_emitted": audit.get("events_emitted", len(events)),
        }
