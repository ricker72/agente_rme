"""
OTBM Node Rules — Canonical hierarchy and validation rules.

This module defines the exact node hierarchy and validation rules
required by Remere's Map Editor based on the Canary source code analysis.

CANONICAL NODE TREE (from Canary iomap_otbm.cpp):
ROOT (OTBM_ROOTV1)
└── MAP_DATA (OTBM_MAP_DATA)
    ├── TILE_AREA (OTBM_TILE_AREA)
    │   ├── TILE (OTBM_TILE)
    │   │   └── ITEM (OTBM_ITEM)
    │   └── HOUSETILE (OTBM_HOUSETILE)
    │
    ├── SPAWNS (OTBM_SPAWNS)
    │   └── SPAWN_AREA (OTBM_SPAWN_AREA)
    │       └── MONSTER (OTBM_MONSTER)
    │
    ├── TOWNS (OTBM_TOWNS)
    │   └── TOWN (OTBM_TOWN)
    │
    └── WAYPOINTS (OTBM_WAYPOINTS)
        └── WAYPOINT (OTBM_WAYPOINT)
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from .otbm_constants import (
    OTBM_ROOTV1,
    OTBM_MAP_DATA,
    OTBM_TILE_AREA,
    OTBM_TILE,
    OTBM_ITEM,
    OTBM_SPAWNS,
    OTBM_SPAWN_AREA,
    OTBM_MONSTER,
    OTBM_TOWNS,
    OTBM_TOWN,
    OTBM_HOUSETILE,
    OTBM_WAYPOINTS,
    OTBM_WAYPOINT,
)


@dataclass
class NodeRule:
    """Validation rule for a specific node type."""

    node_type: int
    name: str
    allowed_parents: List[int]
    allowed_children: List[int]
    is_container: bool = False
    is_required: bool = False
    description: str = ""


@dataclass
class ValidationResult:
    """Result of a single validation check."""

    passed: bool
    message: str
    node_type: Optional[int] = None
    context: str = ""


class NodeValidationRules:
    """
    Defines the canonical OTBM node hierarchy and validation rules
    based on Canary Map Editor v4.0 source code.
    """

    # Define all node rules based on Canary specification
    NODE_RULES: Dict[int, NodeRule] = {
        # Root node - must be first and only one
        OTBM_ROOTV1: NodeRule(
            node_type=OTBM_ROOTV1,
            name="ROOT",
            allowed_parents=[],
            allowed_children=[OTBM_MAP_DATA],
            is_required=True,
            description="OTBM file root node (must be first node in file)",
        ),
        # Map data container
        OTBM_MAP_DATA: NodeRule(
            node_type=OTBM_MAP_DATA,
            name="MAP_DATA",
            allowed_parents=[OTBM_ROOTV1],
            allowed_children=[OTBM_TILE_AREA, OTBM_SPAWNS, OTBM_TOWNS, OTBM_WAYPOINTS],
            is_container=True,
            is_required=True,
            description="Container for all map data sections",
        ),
        # Tile structure
        OTBM_TILE_AREA: NodeRule(
            node_type=OTBM_TILE_AREA,
            name="TILE_AREA",
            allowed_parents=[OTBM_MAP_DATA],
            allowed_children=[OTBM_TILE, OTBM_HOUSETILE],
            is_container=True,
            description="Defines a rectangular area of tiles",
        ),
        OTBM_TILE: NodeRule(
            node_type=OTBM_TILE,
            name="TILE",
            allowed_parents=[OTBM_TILE_AREA],
            allowed_children=[OTBM_ITEM],
            is_container=True,
            description="Individual tile with position and flags",
        ),
        OTBM_ITEM: NodeRule(
            node_type=OTBM_ITEM,
            name="ITEM",
            allowed_parents=[OTBM_TILE],
            allowed_children=[OTBM_ITEM],  # Items can contain other items (containers)
            is_container=True,
            description="Item on a tile (can be ground, objects, or container items)",
        ),
        OTBM_HOUSETILE: NodeRule(
            node_type=OTBM_HOUSETILE,
            name="HOUSETILE",
            allowed_parents=[OTBM_TILE_AREA],
            allowed_children=[],
            description="House tile with house ID reference",
        ),
        # Spawn structure
        OTBM_SPAWNS: NodeRule(
            node_type=OTBM_SPAWNS,
            name="SPAWNS",
            allowed_parents=[OTBM_MAP_DATA],
            allowed_children=[OTBM_SPAWN_AREA],
            is_container=True,
            description="Container for all spawn areas",
        ),
        OTBM_SPAWN_AREA: NodeRule(
            node_type=OTBM_SPAWN_AREA,
            name="SPAWN_AREA",
            allowed_parents=[OTBM_SPAWNS],
            allowed_children=[OTBM_MONSTER],
            is_container=True,
            description="Circular area where monsters can spawn",
        ),
        OTBM_MONSTER: NodeRule(
            node_type=OTBM_MONSTER,
            name="MONSTER",
            allowed_parents=[OTBM_SPAWN_AREA],
            allowed_children=[],
            description="Monster that can spawn in the area",
        ),
        # Town structure
        OTBM_TOWNS: NodeRule(
            node_type=OTBM_TOWNS,
            name="TOWNS",
            allowed_parents=[OTBM_MAP_DATA],
            allowed_children=[OTBM_TOWN],
            is_container=True,
            description="Container for all towns",
        ),
        OTBM_TOWN: NodeRule(
            node_type=OTBM_TOWN,
            name="TOWN",
            allowed_parents=[OTBM_TOWNS],
            allowed_children=[],
            description="Town with ID, name, and temple position",
        ),
        # Waypoint structure
        OTBM_WAYPOINTS: NodeRule(
            node_type=OTBM_WAYPOINTS,
            name="WAYPOINTS",
            allowed_parents=[OTBM_MAP_DATA],
            allowed_children=[OTBM_WAYPOINT],
            is_container=True,
            description="Container for all waypoints",
        ),
        OTBM_WAYPOINT: NodeRule(
            node_type=OTBM_WAYPOINT,
            name="WAYPOINT",
            allowed_parents=[OTBM_WAYPOINTS],
            allowed_children=[],
            description="Named waypoint with position",
        ),
    }

    # Define the canonical hierarchy order
    CANONICAL_CHILDREN_ORDER: Dict[int, List[int]] = {
        OTBM_MAP_DATA: [OTBM_TILE_AREA, OTBM_SPAWNS, OTBM_TOWNS, OTBM_WAYPOINTS],
        OTBM_TILE_AREA: [OTBM_TILE, OTBM_HOUSETILE],
        OTBM_TILE: [OTBM_ITEM],
        OTBM_SPAWNS: [OTBM_SPAWN_AREA],
        OTBM_SPAWN_AREA: [OTBM_MONSTER],
        OTBM_TOWNS: [OTBM_TOWN],
        OTBM_WAYPOINTS: [OTBM_WAYPOINT],
    }

    @classmethod
    def get_rule(cls, node_type: int) -> Optional[NodeRule]:
        """Get validation rule for a node type."""
        return cls.NODE_RULES.get(node_type)

    @classmethod
    def is_valid_parent(cls, child_type: int, parent_type: int) -> bool:
        """Check if a parent-child relationship is valid."""
        rule = cls.get_rule(child_type)
        if not rule:
            return False
        return parent_type in rule.allowed_parents

    @classmethod
    def is_valid_child(cls, parent_type: int, child_type: int) -> bool:
        """Check if a child can be under a parent."""
        rule = cls.get_rule(parent_type)
        if not rule:
            return False
        return child_type in rule.allowed_children

    @classmethod
    def get_required_nodes(cls) -> List[int]:
        """Get list of node types that are required for valid OTBM."""
        return [rule.node_type for rule in cls.NODE_RULES.values() if rule.is_required]

    @classmethod
    def validate_hierarchy(cls, parent_type: int, child_type: int) -> ValidationResult:
        """Validate a parent-child relationship."""
        if not cls.is_valid_child(parent_type, child_type):
            child_rule = cls.get_rule(child_type)
            parent_rule = cls.get_rule(parent_type)

            child_name = child_rule.name if child_rule else f"0x{child_type:02X}"
            parent_name = parent_rule.name if parent_rule else f"0x{parent_type:02X}"

            if child_rule:
                allowed_parents = [
                    parent.name if (parent := cls.get_rule(p)) else f"0x{p:02X}"
                    for p in child_rule.allowed_parents
                ]
                message = (
                    f"Invalid hierarchy: {child_name} (0x{child_type:02X}) "
                    f"cannot be child of {parent_name} (0x{parent_type:02X}). "
                    f"Allowed parents: {', '.join(allowed_parents) if allowed_parents else 'none'}"
                )
            else:
                message = (
                    f"Invalid node type: 0x{child_type:02X} is not a recognized OTBM node type"
                )

            return ValidationResult(False, message, child_type, f"{parent_name}→{child_name}")

        child_rule = cls.get_rule(child_type)
        parent_rule = cls.get_rule(parent_type)
        child_name = child_rule.name if child_rule else f"0x{child_type:02X}"
        parent_name = parent_rule.name if parent_rule else f"0x{parent_type:02X}"
        return ValidationResult(True, f"Valid hierarchy: {child_name} under {parent_name}")

    @classmethod
    def validate_node_order(
        cls, parent_type: int, children_types: List[int]
    ) -> List[ValidationResult]:
        """Validate the order of children nodes."""
        results: List[ValidationResult] = []

        if parent_type not in cls.CANONICAL_CHILDREN_ORDER:
            return results  # No specific order requirement

        expected_order = cls.CANONICAL_CHILDREN_ORDER[parent_type]
        parent_rule = cls.get_rule(parent_type)
        parent_name = parent_rule.name if parent_rule else f"0x{parent_type:02X}"

        # Check if children appear in the expected order
        for i, child_type in enumerate(children_types):
            if child_type not in expected_order:
                continue  # Already validated by hierarchy rules

            # Find expected position
            expected_pos = expected_order.index(child_type)
            # Count how many expected children came before this one
            expected_before = [t for t in expected_order if t in children_types[:i]]
            expected_pos_among_present = len(expected_before)

            if expected_pos_among_present != expected_pos:
                child_rule = cls.get_rule(child_type)
                child_name = child_rule.name if child_rule else f"0x{child_type:02X}"
                prior_names = [
                    rule.name if (rule := cls.get_rule(t)) else f"0x{t:02X}"
                    for t in expected_order
                    if expected_order.index(t) < expected_pos
                ]
                results.append(
                    ValidationResult(
                        False,
                        f"Node ordering issue: {child_name} should appear after "
                        f"{', '.join(prior_names)}",
                        child_type,
                        f"{parent_name} ordering",
                    )
                )

        return results


class CanonicalNodeHierarchy:
    """
    Represents the canonical OTBM node hierarchy as documented in Canary.
    """

    # Text representation of the canonical hierarchy
    CANONICAL_TREE = """
ROOT (OTBM_ROOTV1)
└── MAP_DATA (OTBM_MAP_DATA)
    ├── TILE_AREA (OTBM_TILE_AREA)
    │   ├── TILE (OTBM_TILE)
    │   │   └── ITEM (OTBM_ITEM)
    │   └── HOUSETILE (OTBM_HOUSETILE)
    │
    ├── SPAWNS (OTBM_SPAWNS)
    │   └── SPAWN_AREA (OTBM_SPAWN_AREA)
    │       └── MONSTER (OTBM_MONSTER)
    │
    ├── TOWNS (OTBM_TOWNS)
    │   └── TOWN (OTBM_TOWN)
    │
    └── WAYPOINTS (OTBM_WAYPOINTS)
        └── WAYPOINT (OTBM_WAYPOINT)
"""

    @classmethod
    def get_hierarchy_description(cls) -> str:
        """Get text description of canonical hierarchy."""
        return cls.CANONICAL_TREE.strip()

    @classmethod
    def get_node_validation_rules(cls) -> Dict[int, NodeRule]:
        """Get all node validation rules."""
        return NodeValidationRules.NODE_RULES

    @classmethod
    def get_required_root_nodes(cls) -> List[int]:
        """Get node types that must appear directly under ROOT."""
        return [OTBM_MAP_DATA]

    @classmethod
    def get_optional_root_nodes(cls) -> List[int]:
        """Get node types that can optionally appear under ROOT (none in canonical OTBM)."""
        return []


__all__ = [
    "NodeRule",
    "ValidationResult",
    "NodeValidationRules",
    "CanonicalNodeHierarchy",
]
