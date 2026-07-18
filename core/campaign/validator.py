"""
CampaignValidator — validates a ``CampaignPackage`` (or raw dict) for
Hito 26.1C compliance.

Required top-level keys (per the task contract):
    * ``quests``  — list of quest dicts
    * ``bosses``  — list of boss dicts
    * ``raids``   — list of raid dicts
    * ``story``   — dict with main-story content
    * ``rewards`` — dict with reward summary

The validator never raises — it returns a ``ValidationResult`` carrying
both the boolean ``is_valid`` flag and a structured list of issues.
That makes the validator easy to use in both production code and tests.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .package import CampaignPackage, PackageStatus, REQUIRED_KEYS


class Severity(str, Enum):
    """Severity of a single validation issue."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A single finding reported by the validator."""

    key: str
    severity: Severity
    message: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "key": self.key,
            "severity": self.severity.value,
            "message": self.message,
        }


@dataclass
class ValidationResult:
    """Aggregate result of a validation run."""

    is_valid: bool = True
    issues: List[ValidationIssue] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    validated_at: str = ""

    def __post_init__(self) -> None:
        if not self.validated_at:
            self.validated_at = datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def add_error(self, key: str, message: str) -> None:
        self.issues.append(
            ValidationIssue(key=key, severity=Severity.ERROR, message=message)
        )
        self.is_valid = False

    def add_warning(self, key: str, message: str) -> None:
        self.issues.append(
            ValidationIssue(key=key, severity=Severity.WARNING, message=message)
        )

    def add_info(self, key: str, message: str) -> None:
        self.issues.append(
            ValidationIssue(key=key, severity=Severity.INFO, message=message)
        )

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "issues": [i.to_dict() for i in self.issues],
            "summary": dict(self.summary),
            "validated_at": self.validated_at,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


class CampaignValidator:
    """
    Validates campaign data against the Hito 26.1C contract.

    Accepts either a ``CampaignPackage`` or a plain ``dict``.  Returns a
    ``ValidationResult`` (never raises).
    """

    def validate(
        self,
        campaign: Union[CampaignPackage, Dict[str, Any], None],
    ) -> ValidationResult:
        """Run all validation checks and return a result."""
        result = ValidationResult()
        data = self._coerce(campaign, result)

        if data is None:
            # Coercion already added an error.
            return result

        # 1) Required keys present
        for key in REQUIRED_KEYS:
            if key not in data:
                result.add_error(key, f"Required key '{key}' missing")
            else:
                self._validate_key(key, data[key], result)

        # 2) Status-aware extra checks
        status = self._extract_status(campaign)
        if status == PackageStatus.EMPTY and not any(
            data.get(k) for k in REQUIRED_KEYS
        ):
            result.add_warning(
                "status",
                "CampaignPackage is in EMPTY state and contains no content",
            )

        # 3) Summary
        result.summary = {
            "theme": data.get("theme", "default"),
            "level_range": data.get("level_range", [1, 200]),
            "counts": {
                "quests": self._count(data.get("quests")),
                "bosses": self._count(data.get("bosses")),
                "raids": self._count(data.get("raids")),
                "side_quests": self._count(data.get("side_quests", [])),
            },
            "status": str(status.value) if hasattr(status, "value") else str(status),
            "errors": len(result.errors),
            "warnings": len(result.warnings),
        }
        return result

    # ------------------------------------------------------------------
    # Per-key validators
    # ------------------------------------------------------------------

    def _validate_key(self, key: str, value: Any, result: ValidationResult) -> None:
        if key in ("quests", "bosses", "raids"):
            if not isinstance(value, list):
                result.add_error(
                    key, f"'{key}' must be a list, got {type(value).__name__}"
                )
                return
            if key == "quests" and len(value) == 0:
                result.add_warning(key, "'quests' is empty")
            if key == "bosses" and len(value) == 0:
                result.add_warning(key, "'bosses' is empty")
            if key == "raids" and len(value) == 0:
                result.add_warning(key, "'raids' is empty")
            # Soft check: list items should be dicts
            for i, item in enumerate(value):
                if not isinstance(item, dict):
                    result.add_error(
                        f"{key}[{i}]",
                        f"Item must be a dict, got {type(item).__name__}",
                    )
        elif key == "story":
            if not isinstance(value, dict):
                result.add_error(
                    key, f"'story' must be a dict, got {type(value).__name__}"
                )
        elif key == "rewards":
            if not isinstance(value, dict):
                result.add_error(
                    key, f"'rewards' must be a dict, got {type(value).__name__}"
                )
            # Soft check
            if not value:
                result.add_warning(key, "'rewards' is empty")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _count(value: Any) -> int:
        if isinstance(value, list):
            return len(value)
        if isinstance(value, dict):
            return len(value)
        return 0

    @staticmethod
    def _coerce(
        campaign: Union[CampaignPackage, Dict[str, Any], None],
        result: ValidationResult,
    ) -> Optional[Dict[str, Any]]:
        if campaign is None:
            result.add_error(
                "root", "Campaign is None — pipeline must never produce None"
            )
            return None
        if isinstance(campaign, CampaignPackage):
            return campaign.to_dict()
        if isinstance(campaign, dict):
            return campaign
        result.add_error(
            "root", f"Unsupported campaign type: {type(campaign).__name__}"
        )
        return None

    @staticmethod
    def _extract_status(
        campaign: Union[CampaignPackage, Dict[str, Any], None],
    ) -> PackageStatus:
        if isinstance(campaign, CampaignPackage):
            return campaign.status
        if isinstance(campaign, dict):
            raw = campaign.get("status", "ok")
            try:
                return PackageStatus(raw)
            except ValueError:
                return PackageStatus.OK
        return PackageStatus.EMPTY
