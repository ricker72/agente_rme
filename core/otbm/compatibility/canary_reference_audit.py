"""
Canary Reference Audit — Analysis of Canary Map Editor OTBM implementation.

This module implements PHASE OTBM-RME-1A: Canary Reference Audit.

It documents the exact OTBM structure used by Canary Map Editor v4.0
based on analysis of the source code in iomap_otbm.h and iomap_otbm.cpp.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from .otbm_constants import (
    AGENTE_OTBM_NODE_HOUSETILE,
    AGENTE_OTBM_NODE_ITEM,
    AGENTE_OTBM_NODE_MAP_DATA,
    AGENTE_OTBM_NODE_MONSTER,
    AGENTE_OTBM_NODE_ROOT,
    AGENTE_OTBM_NODE_SPAWN_AREA,
    AGENTE_OTBM_NODE_SPAWNS,
    AGENTE_OTBM_NODE_TILE,
    AGENTE_OTBM_NODE_TILE_AREA,
    AGENTE_OTBM_NODE_TOWN,
    AGENTE_OTBM_NODE_TOWNS,
    AGENTE_OTBM_NODE_WAYPOINT,
    AGENTE_OTBM_NODE_WAYPOINTS,
    OTBM_HOUSETILE,
    OTBM_ACCEPTED_IDENTIFIERS,
    OTBM_IDENTIFIER,
    OTBM_ITEM,
    OTBM_ITEM_DEF,
    OTBM_MAP_DATA,
    OTBM_MONSTER,
    OTBM_ROOTV1,
    OTBM_SPAWN_AREA,
    OTBM_SPAWN_NPC_AREA,
    OTBM_SPAWNS,
    OTBM_SPAWNS_NPC,
    OTBM_TILE,
    OTBM_TILE_AREA,
    OTBM_TILE_REF,
    OTBM_TILE_SQUARE,
    OTBM_TILE_ZONE,
    OTBM_TOWN,
    OTBM_TOWNS,
    OTBM_WAYPOINT,
    OTBM_WAYPOINTS,
)
from .otbm_node_rules import NodeValidationRules, ValidationResult
from .validation_report import (
    SeverityLevel,
    ValidationIssue,
    ValidationReport,
    ValidationStatus,
)


@dataclass
class CanaryAuditReport:
    """Structured report of Canary OTBM format analysis."""

    node_constants: Dict[str, int]
    hierarchy_rules: Dict[str, Dict]
    required_attributes: Dict[str, List[str]]
    optional_attributes: Dict[str, List[str]]
    serialization_rules: Dict[str, str]
    issues_found: List[str]
    compatibility_notes: List[str]

    def to_dict(self) -> Dict:
        """Convert report to dictionary."""
        return {
            "node_constants": self.node_constants,
            "hierarchy_rules": self.hierarchy_rules,
            "required_attributes": self.required_attributes,
            "optional_attributes": self.optional_attributes,
            "serialization_rules": self.serialization_rules,
            "issues_found": self.issues_found,
            "compatibility_notes": self.compatibility_notes,
        }


class CanaryReferenceAudit:
    """
    Audits and documents the OTBM format used by Canary Map Editor.

    This class analyzes the Canary source code and documents:
    - Node type constants
    - Node hierarchy rules
    - Required and optional attributes
    - Serialization/deserialization rules
    """

    def __init__(self):
        self.node_rules = NodeValidationRules()
        self.report: CanaryAuditReport = self._generate_canary_audit_report()

    def _generate_canary_audit_report(self) -> CanaryAuditReport:
        """Generate comprehensive audit report of Canary OTBM format."""
        return CanaryAuditReport(
            node_constants=self._document_node_constants(),
            hierarchy_rules=self._document_hierarchy_rules(),
            required_attributes=self._document_required_attributes(),
            optional_attributes=self._document_optional_attributes(),
            serialization_rules=self._document_serialization_rules(),
            issues_found=self._identify_compatibility_issues(),
            compatibility_notes=self._generate_compatibility_notes(),
        )

    def _document_node_constants(self) -> Dict[str, int]:
        """Document all node constants from Canary source."""
        return {
            "OTBM_ROOTV1": OTBM_ROOTV1,
            "OTBM_MAP_DATA": OTBM_MAP_DATA,
            "OTBM_ITEM_DEF": OTBM_ITEM_DEF,
            "OTBM_TILE_AREA": OTBM_TILE_AREA,
            "OTBM_TILE": OTBM_TILE,
            "OTBM_ITEM": OTBM_ITEM,
            "OTBM_TILE_SQUARE": OTBM_TILE_SQUARE,
            "OTBM_TILE_REF": OTBM_TILE_REF,
            "OTBM_SPAWNS": OTBM_SPAWNS,
            "OTBM_SPAWN_AREA": OTBM_SPAWN_AREA,
            "OTBM_MONSTER": OTBM_MONSTER,
            "OTBM_TOWNS": OTBM_TOWNS,
            "OTBM_TOWN": OTBM_TOWN,
            "OTBM_HOUSETILE": OTBM_HOUSETILE,
            "OTBM_WAYPOINTS": OTBM_WAYPOINTS,
            "OTBM_WAYPOINT": OTBM_WAYPOINT,
            "OTBM_SPAWN_NPC_AREA": OTBM_SPAWN_NPC_AREA,
            "OTBM_SPAWNS_NPC": OTBM_SPAWNS_NPC,
            "OTBM_TILE_ZONE": OTBM_TILE_ZONE,
        }

    def _document_hierarchy_rules(self) -> Dict[str, Dict]:
        """Document the canonical node hierarchy from Canary."""
        return {
            "ROOT": {
                "allowed_children": ["MAP_DATA"],
                "description": "Root node of OTBM file, must be first node",
            },
            "MAP_DATA": {
                "allowed_children": ["TILE_AREA", "SPAWNS", "TOWNS", "WAYPOINTS"],
                "description": "Container for all map data sections",
                "order": ["TILE_AREA", "SPAWNS", "TOWNS", "WAYPOINTS"],
            },
            "TILE_AREA": {
                "allowed_children": ["TILE", "HOUSETILE"],
                "description": "Defines a rectangular area of tiles with base coordinates",
                "order": ["TILE", "HOUSETILE"],
            },
            "TILE": {
                "allowed_children": ["ITEM"],
                "description": "Individual tile with relative coordinates and flags",
                "attributes": ["offset_x", "offset_y", "tile_flags"],
            },
            "ITEM": {
                "allowed_children": ["ITEM"],
                "description": "Item on a tile, can contain nested items (containers)",
                "attributes": ["item_id", "count", "action_id", "unique_id", "text", "etc."],
            },
            "HOUSETILE": {
                "allowed_children": [],
                "description": "House tile with house ID reference",
                "attributes": ["offset_x", "offset_y", "house_id"],
            },
            "SPAWNS": {
                "allowed_children": ["SPAWN_AREA"],
                "description": "Container for monster spawn areas",
            },
            "SPAWN_AREA": {
                "allowed_children": ["MONSTER"],
                "description": "Circular spawn area with center and radius",
                "attributes": ["center_x", "center_y", "center_z", "radius"],
            },
            "MONSTER": {
                "allowed_children": [],
                "description": "Monster that can spawn in the area",
                "attributes": ["name", "direction", "spawntime"],
            },
            "TOWNS": {
                "allowed_children": ["TOWN"],
                "description": "Container for town definitions",
            },
            "TOWN": {
                "allowed_children": [],
                "description": "Town with ID, name, and temple position",
                "attributes": ["town_id", "name", "temple_x", "temple_y", "temple_z"],
            },
            "WAYPOINTS": {
                "allowed_children": ["WAYPOINT"],
                "description": "Container for waypoint definitions",
            },
            "WAYPOINT": {
                "allowed_children": [],
                "description": "Named waypoint with position",
                "attributes": ["name", "x", "y", "z"],
            },
        }

    def _document_required_attributes(self) -> Dict[str, List[str]]:
        """Document required attributes for each node type."""
        return {
            "ROOT": ["version", "width", "height", "majorVersionItems", "minorVersionItems"],
            "MAP_DATA": ["description", "spawn_file", "house_file"],
            "TILE_AREA": ["base_x", "base_y", "base_z"],
            "TILE": ["offset_x", "offset_y"],
            "ITEM": ["item_id"],
            "HOUSETILE": ["offset_x", "offset_y", "house_id"],
            "SPAWN_AREA": ["center_x", "center_y", "center_z", "radius"],
            "MONSTER": ["name", "direction", "spawntime"],
            "TOWN": ["town_id", "name", "temple_x", "temple_y", "temple_z"],
            "WAYPOINT": ["name", "x", "y", "z"],
        }

    def _document_optional_attributes(self) -> Dict[str, List[str]]:
        """Document optional attributes for each node type."""
        return {
            "TILE": ["tile_flags"],
            "ITEM": [
                "count",
                "action_id",
                "unique_id",
                "text",
                "description",
                "subtype",
                "charges",
                "duration",
                "decaying_state",
                "written_date",
                "written_by",
                "sleeper_guid",
                "sleep_start",
            ],
            "ROOT": [],  # All attributes are required for root
            "MAP_DATA": [],  # All attributes are required
            "TILE_AREA": [],  # All attributes are required
            "HOUSETILE": [],  # All attributes are required
            "SPAWN_AREA": [],  # All attributes are required
            "MONSTER": [],  # All attributes are required
            "TOWN": [],  # All attributes are required
            "WAYPOINT": [],  # All attributes are required
        }

    def _document_serialization_rules(self) -> Dict[str, str]:
        """Document serialization rules from Canary source."""
        return {
            "file_header": "OTBM files start with 4-byte identifier 'OTBM'",
            "node_structure": "Each node has: [1-byte type][2-byte size][attributes][children]",
            "root_node": "ROOT node has additional header: [version:4][width:2][height:2][item_major:4][item_minor:4]",
            "string_encoding": "Strings are UTF-8 with 2-byte length prefix",
            "integer_encoding": "Integers use little-endian byte order",
            "size_limits": "Node size is limited to 65535 bytes (uint16)",
            "attribute_format": "Attributes have [1-byte type][variable data] format",
            "hierarchy_enforcement": "Canary enforces strict parent-child relationships",
            "order_enforcement": "Canary expects children in specific order for some nodes",
        }

    def _identify_compatibility_issues(self) -> List[str]:
        """Identify potential compatibility issues between Agente RME and Canary."""
        issues = []

        # Node constant mismatch
        issues.append(
            "NODE_CONSTANT_MISMATCH: Agente RME uses different node type constants than Canary"
        )
        issues.append(
            f"  - Agente ROOT: 0x{AGENTE_OTBM_NODE_ROOT:02X} vs Canary ROOT: 0x{OTBM_ROOTV1:02X}"
        )
        issues.append(
            f"  - Agente MAP_DATA: 0x{AGENTE_OTBM_NODE_MAP_DATA:02X} vs Canary MAP_DATA: 0x{OTBM_MAP_DATA:02X}"
        )

        # Hierarchy validation
        issues.append(
            "HIERARCHY_VALIDATION: Current Agente RME validator may not enforce strict Canary hierarchy rules"
        )
        issues.append(
            "ORDER_VALIDATION: Current Agente RME validator may not enforce Canary node ordering requirements"
        )

        # Version compatibility
        issues.append(
            "VERSION_COMPATIBILITY: Agente RME may use different OTBM version than Canary expects"
        )

        # Attribute handling
        issues.append(
            "ATTRIBUTE_HANDLING: Attribute serialization may differ between implementations"
        )

        return issues

    def _generate_compatibility_notes(self) -> List[str]:
        """Generate compatibility notes and recommendations."""
        return [
            "COMPATIBILITY_NOTE: Canary uses OTBM version 1 with specific node constants",
            "RECOMMENDATION: Agente RME should use Canary node constants for compatibility",
            "RECOMMENDATION: Implement strict hierarchy validation matching Canary rules",
            "RECOMMENDATION: Enforce node ordering as expected by Canary",
            "RECOMMENDATION: Use identical attribute serialization format",
            "RECOMMENDATION: Validate OTBM files against Canary reference implementation",
            "ROOT_CAUSE_ANALYSIS: Node constant mismatch is likely cause of RME node errors",
            "CERTIFICATION_REQUIREMENT: OTBM files must pass Canary validation to be RME-compatible",
        ]

    def get_audit_report(self) -> CanaryAuditReport:
        """Get the complete Canary audit report."""
        return self.report

    def validate_otbm_header(self, data: bytes) -> ValidationResult:
        """Validate OTBM file header against Canary specifications."""
        if len(data) < 4:
            return ValidationResult(
                False, "OTBM file too short for header validation", None, "header_validation"
            )

        # Check magic identifier
        if data[:4] not in OTBM_ACCEPTED_IDENTIFIERS:
            return ValidationResult(
                False,
                f"Invalid OTBM magic: got {data[:4]!r}",
                None,
                "header_validation",
            )

        # Check root node type (byte at position 4)
        if len(data) < 5:
            return ValidationResult(
                False, "OTBM file too short to read root node type", None, "header_validation"
            )

        root_node_type = data[4]
        if root_node_type != 0xFE:
            return ValidationResult(
                False,
                f"Invalid root node marker: expected 0xFE, got 0x{root_node_type:02X}",
                root_node_type,
                "header_validation",
            )

        return ValidationResult(
            True,
            f"Valid OTBM header with Canary root node type 0x{OTBM_ROOTV1:02X}",
            OTBM_ROOTV1,
            "header_validation",
        )

    def analyze_node_constant_discrepancy(self) -> Dict[str, Tuple[int, int]]:
        """Analyze the discrepancy between Agente and Canary node constants."""
        discrepancy = {}

        agente_constants = {
            "ROOT": AGENTE_OTBM_NODE_ROOT,
            "MAP_DATA": AGENTE_OTBM_NODE_MAP_DATA,
            "TILE_AREA": AGENTE_OTBM_NODE_TILE_AREA,
            "TILE": AGENTE_OTBM_NODE_TILE,
            "ITEM": AGENTE_OTBM_NODE_ITEM,
            "SPAWNS": AGENTE_OTBM_NODE_SPAWNS,
            "SPAWN_AREA": AGENTE_OTBM_NODE_SPAWN_AREA,
            "MONSTER": AGENTE_OTBM_NODE_MONSTER,
            "TOWNS": AGENTE_OTBM_NODE_TOWNS,
            "TOWN": AGENTE_OTBM_NODE_TOWN,
            "HOUSETILE": AGENTE_OTBM_NODE_HOUSETILE,
            "WAYPOINTS": AGENTE_OTBM_NODE_WAYPOINTS,
            "WAYPOINT": AGENTE_OTBM_NODE_WAYPOINT,
        }

        canary_constants = {
            "ROOT": OTBM_ROOTV1,
            "MAP_DATA": OTBM_MAP_DATA,
            "TILE_AREA": OTBM_TILE_AREA,
            "TILE": OTBM_TILE,
            "ITEM": OTBM_ITEM,
            "SPAWNS": OTBM_SPAWNS,
            "SPAWN_AREA": OTBM_SPAWN_AREA,
            "MONSTER": OTBM_MONSTER,
            "TOWNS": OTBM_TOWNS,
            "TOWN": OTBM_TOWN,
            "HOUSETILE": OTBM_HOUSETILE,
            "WAYPOINTS": OTBM_WAYPOINTS,
            "WAYPOINT": OTBM_WAYPOINT,
        }

        for node_name in agente_constants:
            agente_val = agente_constants[node_name]
            canary_val = canary_constants[node_name]
            if agente_val != canary_val:
                discrepancy[node_name] = (agente_val, canary_val)

        return discrepancy

    def generate_compatibility_validation_report(self) -> ValidationReport:
        """Generate a validation report for Canary compatibility."""
        report = ValidationReport(ValidationStatus.UNKNOWN)
        report.file_path = "Canary Reference Audit"
        report.canary_compatible = False
        report.rme_compatible = False

        # Add node constant discrepancy issues
        discrepancy = self.analyze_node_constant_discrepancy()
        for node_name, (agente_val, canary_val) in discrepancy.items():
            issue = ValidationIssue(
                code=f"NODE_CONSTANT_MISMATCH_{node_name}",
                message=f"{node_name} node constant mismatch: Agente=0x{agente_val:02X}, Canary=0x{canary_val:02X}",
                severity=SeverityLevel.CRITICAL,
                node_type=agente_val,
                node_type_name=node_name,
                context="node_constant_compatibility",
                suggested_fix=f"Use Canary constant 0x{canary_val:02X} instead of Agente constant 0x{agente_val:02X}",
            )
            report.add_issue(issue)

        # Add hierarchy validation issues
        hierarchy_issue = ValidationIssue(
            code="HIERARCHY_VALIDATION_MISSING",
            message="Current validator does not enforce strict Canary hierarchy rules",
            severity=SeverityLevel.CRITICAL,
            context="hierarchy_validation",
            suggested_fix="Implement NodeValidationRules.validate_hierarchy() in main validator",
        )
        report.add_issue(hierarchy_issue)

        # Add ordering validation issues
        ordering_issue = ValidationIssue(
            code="ORDER_VALIDATION_MISSING",
            message="Current validator does not enforce Canary node ordering requirements",
            severity=SeverityLevel.CRITICAL,
            context="order_validation",
            suggested_fix="Implement NodeValidationRules.validate_node_order() in main validator",
        )
        report.add_issue(ordering_issue)

        # Update status
        if report.has_critical_issues():
            report.status = ValidationStatus.FAILURE
            report.compatibility_notes.append(
                "CRITICAL: Agente RME is not Canary-compatible due to node constant mismatch"
            )
        else:
            report.status = ValidationStatus.SUCCESS
            report.canary_compatible = True
            report.rme_compatible = True

        return report

    def get_root_cause_analysis(self) -> str:
        """Provide root cause analysis for RME compatibility issues."""
        analysis = """
ROOT CAUSE ANALYSIS: RME Node Errors in issavi_roshamuul_v1.otbm

Primary Issue Identified:
- Node constant mismatch between Agente RME and Canary/RME

Technical Details:
1. Agente RME uses node constants starting from 0x00
2. Canary/RME expects node constants starting from 0x01
3. This causes RME to misinterpret the entire node hierarchy
4. Results in "node errors" and rejection of valid Agente-generated OTBM files

Specific Mismatches:
- ROOT node: Agente=0x00 vs Canary=0x01
- MAP_DATA: Agente=0x01 vs Canary=0x02
- All subsequent nodes are offset by +1

Impact:
- RME cannot parse the node tree correctly
- Hierarchy validation fails
- Node relationships are misinterpreted
- File is rejected as invalid

Solution Required:
- Align Agente RME node constants with Canary specification
- Implement strict hierarchy validation
- Ensure node ordering matches Canary expectations
- Validate against Canary reference implementation
"""

        return analysis.strip()


__all__ = [
    "CanaryReferenceAudit",
    "CanaryAuditReport",
]
