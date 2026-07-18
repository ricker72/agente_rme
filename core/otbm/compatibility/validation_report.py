"""
Validation Report — Structured reporting for OTBM compatibility validation.

This module provides data structures for reporting validation results
in a structured, machine-readable format.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from typing import Dict, List, Optional

from .otbm_node_rules import ValidationResult


class ValidationStatus(Enum):
    """Status of a validation operation."""

    SUCCESS = "success"
    WARNING = "warning"
    FAILURE = "failure"
    UNKNOWN = "unknown"


class SeverityLevel(Enum):
    """Severity level of validation issues."""

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


@dataclass
class ValidationIssue:
    """Individual validation issue found during OTBM analysis."""

    code: str
    message: str
    severity: SeverityLevel
    node_type: Optional[int] = None
    node_type_name: Optional[str] = None
    context: str = ""
    position: Optional[int] = None
    suggested_fix: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "node_type": self.node_type,
            "node_type_name": self.node_type_name,
            "context": self.context,
            "position": self.position,
            "suggested_fix": self.suggested_fix,
        }


@dataclass
class ValidationStatistics:
    """Statistics about the validated OTBM file."""

    total_nodes: int = 0
    tiles: int = 0
    items: int = 0
    spawn_areas: int = 0
    monsters: int = 0
    towns: int = 0
    waypoints: int = 0
    house_tiles: int = 0
    file_size: int = 0
    version: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    item_version: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_nodes": self.total_nodes,
            "tiles": self.tiles,
            "items": self.items,
            "spawn_areas": self.spawn_areas,
            "monsters": self.monsters,
            "towns": self.towns,
            "waypoints": self.waypoints,
            "house_tiles": self.house_tiles,
            "file_size": self.file_size,
            "version": self.version,
            "width": self.width,
            "height": self.height,
            "item_version": self.item_version,
        }


@dataclass
class ValidationReport:
    """Comprehensive validation report for OTBM compatibility analysis."""

    status: ValidationStatus
    issues: List[ValidationIssue] = field(default_factory=list)
    statistics: ValidationStatistics = field(default_factory=ValidationStatistics)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    file_path: Optional[str] = None
    canary_compatible: bool = False
    rme_compatible: bool = False
    validation_duration_ms: Optional[float] = None
    compatibility_notes: List[str] = field(default_factory=list)

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add a validation issue to the report."""
        self.issues.append(issue)

    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues."""
        return any(issue.severity == SeverityLevel.CRITICAL for issue in self.issues)

    def has_errors(self) -> bool:
        """Check if there are any error-level issues."""
        return any(
            issue.severity in (SeverityLevel.CRITICAL, SeverityLevel.ERROR) for issue in self.issues
        )

    def get_issues_by_severity(self, severity: SeverityLevel) -> List[ValidationIssue]:
        """Get issues filtered by severity level."""
        return [issue for issue in self.issues if issue.severity == severity]

    def to_dict(self) -> Dict:
        """Convert the entire report to a dictionary."""
        return {
            "status": self.status.value,
            "canary_compatible": self.canary_compatible,
            "rme_compatible": self.rme_compatible,
            "file_path": self.file_path,
            "timestamp": self.timestamp,
            "validation_duration_ms": self.validation_duration_ms,
            "statistics": self.statistics.to_dict(),
            "issues": [issue.to_dict() for issue in self.issues],
            "summary": {
                "total_issues": len(self.issues),
                "critical": len(self.get_issues_by_severity(SeverityLevel.CRITICAL)),
                "errors": len(self.get_issues_by_severity(SeverityLevel.ERROR)),
                "warnings": len(self.get_issues_by_severity(SeverityLevel.WARNING)),
                "info": len(self.get_issues_by_severity(SeverityLevel.INFO)),
            },
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert the report to JSON format."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save_to_file(self, file_path: str) -> None:
        """Save the validation report to a JSON file."""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def from_validation_results(cls, results: List[ValidationResult]) -> "ValidationReport":
        """Create a validation report from a list of validation results."""
        report = cls(ValidationStatus.SUCCESS)

        for result in results:
            if not result.passed:
                if "critical" in result.message.lower() or "required" in result.message.lower():
                    severity = SeverityLevel.CRITICAL
                elif "invalid" in result.message.lower() or "error" in result.message.lower():
                    severity = SeverityLevel.ERROR
                elif "warning" in result.message.lower():
                    severity = SeverityLevel.WARNING
                else:
                    severity = SeverityLevel.INFO

                issue = ValidationIssue(
                    code=f"OTBM_{result.context.replace(' ', '_').upper()}",
                    message=result.message,
                    severity=severity,
                    node_type=result.node_type,
                    context=result.context,
                )
                report.add_issue(issue)

        # Update status based on issues
        if report.has_critical_issues():
            report.status = ValidationStatus.FAILURE
        elif report.has_errors():
            report.status = ValidationStatus.FAILURE
        elif len(report.issues) > 0:
            report.status = ValidationStatus.WARNING
        else:
            report.status = ValidationStatus.SUCCESS

        return report


def create_compatibility_issue(
    code: str,
    message: str,
    severity: SeverityLevel,
    node_type: Optional[int] = None,
    node_type_name: Optional[str] = None,
    context: str = "",
    suggested_fix: str = "",
) -> ValidationIssue:
    """Helper function to create a standardized validation issue."""
    return ValidationIssue(
        code=code,
        message=message,
        severity=severity,
        node_type=node_type,
        node_type_name=node_type_name,
        context=context,
        suggested_fix=suggested_fix,
    )


__all__ = [
    "ValidationStatus",
    "SeverityLevel",
    "ValidationIssue",
    "ValidationStatistics",
    "ValidationReport",
    "create_compatibility_issue",
]
