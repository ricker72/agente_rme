"""
OTBM Compatibility Layer — Canary/RME Compatibility Audit.

This package implements OTBM-RME-1: Canary/RME Compatibility Audit.

Key Components:
- CanaryReferenceAudit: Documents canonical OTBM structure from Canary source
- RMECompatibilityValidator: Validates OTBM files against RME requirements
- ExporterAudit: Audits current Agente RME exporter output
- ValidationReport: Structured compatibility reporting

The goal is to ensure Agente RME generates OTBM files that are 100% compatible
with Remere's Map Editor by following the exact format used by Canary.
"""

from .canary_reference_audit import CanaryAuditReport, CanaryReferenceAudit
from .exporter_audit import ExporterAudit, ExporterAuditReport
from .otbm_constants import (
    OTBM_HOUSETILE,
    OTBM_ITEM,
    OTBM_MAP_DATA,
    OTBM_MONSTER,
    OTBM_ROOTV1,
    OTBM_SPAWN_AREA,
    OTBM_SPAWNS,
    OTBM_TILE,
    OTBM_TILE_AREA,
    OTBM_TOWN,
    OTBM_TOWNS,
    OTBM_WAYPOINT,
    OTBM_WAYPOINTS,
)
from .otbm_node_rules import CanonicalNodeHierarchy, NodeValidationRules
from .otbm_node_rules import ValidationResult as NodeValidationResult
from .rme_compatibility_validator import RMECompatibilityValidator
from .validation_report import ValidationReport

ValidationResult = NodeValidationResult

__all__ = [
    # Constants
    "OTBM_ROOTV1",
    "OTBM_MAP_DATA",
    "OTBM_TILE_AREA",
    "OTBM_TILE",
    "OTBM_ITEM",
    "OTBM_SPAWNS",
    "OTBM_SPAWN_AREA",
    "OTBM_MONSTER",
    "OTBM_TOWNS",
    "OTBM_TOWN",
    "OTBM_HOUSETILE",
    "OTBM_WAYPOINTS",
    "OTBM_WAYPOINT",
    # Node rules and validation
    "CanonicalNodeHierarchy",
    "NodeValidationRules",
    "ValidationReport",
    "ValidationResult",
    # Core components
    "CanaryReferenceAudit",
    "CanaryAuditReport",
    "RMECompatibilityValidator",
    "ExporterAudit",
    "ExporterAuditReport",
]
