"""
CriticIssue — represents a detected problem in a map.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class IssueType(str, enum.Enum):
    """Catalog of issues the critic can detect."""

    EMPTY_REGION = "empty_region"
    ISOLATED_REGION = "isolated_region"
    LOW_SPAWN_DENSITY = "low_spawn_density"
    OVERDECORATED_AREA = "overdecorated_area"
    UNDERDECORATED_AREA = "underdecorated_area"
    POOR_NAVIGATION = "poor_navigation"
    INVALID_BOSS_ROOM = "invalid_boss_room"
    CITY_MISSING_SERVICES = "city_missing_services"
    DEAD_END = "dead_end"
    BOTTLENECK = "bottleneck"
    BROKEN_PATH = "broken_path"
    INACCESSIBLE_ZONE = "inaccessible_zone"
    SPAWN_CLUSTER = "spawn_cluster"
    HUNT_GAP = "hunt_gap"
    BOSS_NO_ESCAPE = "boss_no_escape"
    BOSS_TOO_SMALL = "boss_too_small"
    MISSING_DEPOT = "missing_depot"
    MISSING_TEMPLE = "missing_temple"
    MISSING_NPC = "missing_npc"
    DISCONNECTED_STREETS = "disconnected_streets"
    UNREACHABLE_GOAL = "unreachable_goal"


class IssueSeverity(str, enum.Enum):
    """Severity classification for issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# Severity heuristic for known issue types
_DEFAULT_SEVERITY: Dict[IssueType, IssueSeverity] = {
    IssueType.EMPTY_REGION: IssueSeverity.WARNING,
    IssueType.ISOLATED_REGION: IssueSeverity.CRITICAL,
    IssueType.LOW_SPAWN_DENSITY: IssueSeverity.WARNING,
    IssueType.OVERDECORATED_AREA: IssueSeverity.WARNING,
    IssueType.UNDERDECORATED_AREA: IssueSeverity.WARNING,
    IssueType.POOR_NAVIGATION: IssueSeverity.ERROR,
    IssueType.INVALID_BOSS_ROOM: IssueSeverity.CRITICAL,
    IssueType.CITY_MISSING_SERVICES: IssueSeverity.ERROR,
    IssueType.DEAD_END: IssueSeverity.INFO,
    IssueType.BOTTLENECK: IssueSeverity.WARNING,
    IssueType.BROKEN_PATH: IssueSeverity.CRITICAL,
    IssueType.INACCESSIBLE_ZONE: IssueSeverity.CRITICAL,
    IssueType.SPAWN_CLUSTER: IssueSeverity.WARNING,
    IssueType.HUNT_GAP: IssueSeverity.WARNING,
    IssueType.BOSS_NO_ESCAPE: IssueSeverity.WARNING,
    IssueType.BOSS_TOO_SMALL: IssueSeverity.ERROR,
    IssueType.MISSING_DEPOT: IssueSeverity.ERROR,
    IssueType.MISSING_TEMPLE: IssueSeverity.ERROR,
    IssueType.MISSING_NPC: IssueSeverity.WARNING,
    IssueType.DISCONNECTED_STREETS: IssueSeverity.ERROR,
    IssueType.UNREACHABLE_GOAL: IssueSeverity.CRITICAL,
}


@dataclass
class CriticIssue:
    """
    A single detected issue in the map.

    Attributes:
        issue_type: Type of issue (from IssueType enum).
        severity: Severity classification.
        category: The critic category that raised it (e.g. "spawn").
        location: Optional human-readable location (e.g. "north_hunt").
        message: Short human description.
        details: Optional dict with quantitative details.
    """

    issue_type: IssueType
    category: str
    message: str
    severity: IssueSeverity = IssueSeverity.WARNING
    location: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.issue_type, str):
            self.issue_type = IssueType(self.issue_type)
        if isinstance(self.severity, str):
            self.severity = IssueSeverity(self.severity)

    @property
    def penalty(self) -> float:
        """
        Numeric penalty (0-20) deducted from a category score.

        Higher for more severe issues.
        """
        return {
            IssueSeverity.INFO: 1.0,
            IssueSeverity.WARNING: 5.0,
            IssueSeverity.ERROR: 10.0,
            IssueSeverity.CRITICAL: 20.0,
        }.get(self.severity, 5.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_type": self.issue_type.value,
            "severity": self.severity.value,
            "category": self.category,
            "location": self.location,
            "message": self.message,
            "details": self.details,
            "penalty": self.penalty,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CriticIssue":
        return cls(
            issue_type=data.get("issue_type", IssueType.EMPTY_REGION),
            category=data.get("category", "general"),
            message=data.get("message", ""),
            severity=data.get("severity", IssueSeverity.WARNING),
            location=data.get("location", ""),
            details=data.get("details", {}) or {},
        )

    @staticmethod
    def default_severity(issue_type: IssueType) -> IssueSeverity:
        return _DEFAULT_SEVERITY.get(issue_type, IssueSeverity.WARNING)
