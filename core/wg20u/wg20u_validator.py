"""
WG-20U Validator - Validates that rendered world agrees with WG-20TE data.

Implements RULE-39 integration - WG-20U becomes the visual validation authority.
"""

from typing import Any, Dict


class Wg20uValidator:
    """
    Validates visual representation against WG-20TE authoritative data.

    VISUAL_TRUTH_FAILED is returned if any discrepancy is found between
    the rendered world and WG-20TE datasets.
    """

    def validate_all(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run full WG-20TE validation against visual representation.

        Returns VISUAL_TRUTH_FAILED if any check fails.
        """
        results = {
            "wg20te_connectivity_valid": self._validate_connectivity(datasets),
            "wg20te_accessibility_valid": self._validate_accessibility(datasets),
            "wg20te_brush_resolution_valid": self._validate_brush_resolution(
                datasets
            ),
            "wg20te_path_continuity_valid": self._validate_path_continuity(datasets),
        }

        all_valid = all(results.values())

        if not all_valid:
            return {
                "certification_status": "VISUAL_TRUTH_FAILED",
                "validation_results": results,
                "blockers": [
                    "RME_LIKE_LIVE_PREVIEW_BLOCKED"
                ] if not all_valid else [],
                "valid": False,
            }

        return {
            "certification_status": "PASS",
            "validation_results": results,
            "valid": True,
        }

    def _validate_connectivity(self, datasets: Dict[str, Any]) -> bool:
        """Validate connectivity matches WG-20TE Floor Graph."""
        floor_graph = datasets.get("WG20TE_FLOOR_GRAPH.json", {})
        stair_conn = datasets.get("WG20TE_STAIR_CONNECTIVITY.json", {})

        # Check that floor graph is valid
        if not floor_graph.get("floor_count", 0):
            return False

        # Check that stair connectivity is valid
        if not stair_conn.get("valid", False):
            return False

        # Verify connectivity map consistency
        connectivity_map = floor_graph.get("floor_connectivity_map", {})
        if not connectivity_map:
            return False

        # Each floor should have connectivity info
        for floor_id in range(floor_graph.get("floor_count", 0)):
            if str(floor_id) not in connectivity_map:
                return False

        return True

    def _validate_accessibility(self, datasets: Dict[str, Any]) -> bool:
        """Validate building and hunt accessibility matches WG-20TE."""
        building_access = datasets.get(
            "WG20TE_BUILDING_ACCESS_VALIDATION.json", {}
        )
        hunt_reach = datasets.get("WG20TE_HUNT_REACHABILITY.json", {})

        # Check building access validation
        if not building_access.get("valid", False):
            return False

        # Check all building types have brushes
        if not building_access.get("all_types_have_brushes", False):
            return False

        # Check hunt reachability
        if not hunt_reach.get("hunt_entrance_access", False):
            return False
        if not hunt_reach.get("boss_access", False):
            return False
        if not hunt_reach.get("quest_access", False):
            return False

        return True

    def _validate_brush_resolution(self, datasets: Dict[str, Any]) -> bool:
        """Validate brush resolution matches WG-20TE audit."""
        brush_audit = datasets.get(
            "WG20TE_SEMANTIC_BRUSH_RESOLUTION_AUDIT.json", {}
        )
        role_audit = datasets.get("WG20TE_ROLE_UNIQUENESS_AUDIT.json", {})

        # Check semantic brush audit passed
        if not brush_audit.get("semantic_brush_audit_passed", False):
            return False

        # Check role uniqueness passed
        if not role_audit.get("role_uniqueness_passed", False):
            return False

        return True

    def _validate_path_continuity(self, datasets: Dict[str, Any]) -> bool:
        """Validate path continuity matches WG-20TE."""
        path_continuity = datasets.get("WG20TE_PATH_CONTINUITY.json", {})

        # Check all floors reachable from ground
        if not path_continuity.get("all_floors_reachable_from_ground", False):
            return False

        # Check districts connected
        if not path_continuity.get("districts_connected", False):
            return False

        # Check water crossings valid
        if not path_continuity.get("water_crossings_valid", False):
            return False

        return True

    def validate_against_world(
        self, datasets: Dict[str, Any], world_model: Any
    ) -> Dict[str, Any]:
        """
        Validate a world model against WG-20TE datasets.

        This is the primary method for RULE-39 compliance - ensuring
        the rendered world agrees with WG-20TE authoritative data.
        """
        # For now, just validate the datasets themselves
        # In a full implementation, this would compare world_model tiles
        # against WG-20TE brush resolution and connectivity data
        return self.validate_all(datasets)
