from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ConstraintSeverity(Enum):
    FATAL = "fatal"  # Must pass or design is invalid
    REQUIRED = "required"  # Should pass; high priority
    OPTIONAL = "optional"  # Nice-to-have; can be relaxed


@dataclass
class DesignConstraint:
    """A single design constraint with validation logic."""

    name: str
    category: str  # "level", "size", "theme", "difficulty"
    description: str
    severity: ConstraintSeverity
    validator: Optional[str] = None  # Name of validation function
    params: Dict[str, Any] = field(default_factory=dict)
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "severity": self.severity.value,
            "params": self.params,
            "violations": self.violations,
        }


@dataclass
class ConstraintValidationResult:
    """Result of validating constraints against a design."""

    passed: bool
    total: int = 0
    passed_count: int = 0
    failed: List[DesignConstraint] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "total": self.total,
            "passed_count": self.passed_count,
            "failed": [c.name for c in self.failed],
            "errors": self.errors,
            "warnings": self.warnings,
        }


class ConstraintEngine:
    """
    Applies design constraints to ensure coherent world building.

    Constraint categories:
      - level: appropriate for target player levels
      - size: proportional and fit within world bounds
      - theme: visually and thematically consistent
      - difficulty: balanced for intended challenge

    Constraints are checked before any generation happens.
    """

    # Built-in constraint profiles
    CONSTRAINT_PROFILES = {
        "newbie_area": {
            "level": {"min_level": 1, "max_level": 30, "monster_xp_range": (0, 150)},
            "size": {
                "min_width": 10,
                "max_width": 50,
                "min_height": 10,
                "max_height": 50,
            },
            "theme": {"themes": ["green", "tutorial", "safe"]},
            "difficulty": {"max_difficulty": 2, "no_bosses": True},
        },
        "mid_hunt": {
            "level": {
                "min_level": 50,
                "max_level": 150,
                "monster_xp_range": (150, 800),
            },
            "size": {
                "min_width": 20,
                "max_width": 100,
                "min_height": 20,
                "max_height": 100,
            },
            "theme": {"themes": ["cave", "dungeon", "forest", "desert"]},
            "difficulty": {"max_difficulty": 5},
        },
        "high_end_hunt": {
            "level": {
                "min_level": 150,
                "max_level": 400,
                "monster_xp_range": (800, 5000),
            },
            "size": {
                "min_width": 30,
                "max_width": 200,
                "min_height": 30,
                "max_height": 200,
            },
            "theme": {"themes": ["roshamuul", "issavi", "prison", "corruption"]},
            "difficulty": {"max_difficulty": 8},
        },
        "boss_room": {
            "level": {
                "min_level": 100,
                "max_level": 999,
                "monster_xp_range": (5000, 50000),
            },
            "size": {
                "min_width": 8,
                "max_width": 30,
                "min_height": 8,
                "max_height": 30,
            },
            "theme": {"themes": ["dark", "epic", "boss"]},
            "difficulty": {"max_difficulty": 10, "min_difficulty": 6},
        },
        "city": {
            "level": {"min_level": 1, "max_level": 999},
            "size": {
                "min_width": 20,
                "max_width": 300,
                "min_height": 20,
                "max_height": 300,
            },
            "theme": {"themes": ["medieval", "oriental", "desert", "port"]},
            "difficulty": {"max_difficulty": 1, "no_spawns": True},
        },
        "quest_zone": {
            "level": {"min_level": 20, "max_level": 500},
            "size": {
                "min_width": 10,
                "max_width": 80,
                "min_height": 10,
                "max_height": 80,
            },
            "theme": {"themes": ["magic", "library", "dungeon", "temple"]},
            "difficulty": {"max_difficulty": 7, "chests": True},
        },
    }

    def __init__(self):
        self._constraints: List[DesignConstraint] = []
        self._active_profile: Optional[str] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_profile(self, profile_name: str) -> List[DesignConstraint]:
        """
        Load a predefined constraint profile.

        Profiles: newbie_area, mid_hunt, high_end_hunt, boss_room, city, quest_zone
        """
        if profile_name not in self.CONSTRAINT_PROFILES:
            return []

        profile = self.CONSTRAINT_PROFILES[profile_name]
        self._active_profile = profile_name
        self._constraints = []
        self._extract_constraints_from_profile(profile, profile_name)

        return self._constraints

    def add_constraint(self, constraint: DesignConstraint) -> None:
        self._constraints.append(constraint)

    def set_constraints(self, constraints: List[DesignConstraint]) -> None:
        self._constraints = list(constraints)

    def get_constraints(self, category: Optional[str] = None) -> List[DesignConstraint]:
        if category:
            return [c for c in self._constraints if c.category == category]
        return list(self._constraints)

    def constraints_by_type(self) -> Dict[str, List[DesignConstraint]]:
        categories: Dict[str, List[DesignConstraint]] = {}
        for c in self._constraints:
            categories.setdefault(c.category, []).append(c)
        return categories

    def validate(self, design_context: Dict[str, Any]) -> ConstraintValidationResult:
        """
        Validate all constraints against a design context.

        Args:
            design_context: Dict with keys like:
                - "level": target player level
                - "width", "height": map dimensions
                - "theme": theme name
                - "difficulty": difficulty rating (1-10)
                - "has_boss": bool
                - "has_spawns": bool
                - "monster_xp": list of XP values
                - "zone_count": int

        Returns:
            ConstraintValidationResult with pass/fail and violations.
        """
        total = len(self._constraints)
        passed_count = 0
        failed: List[DesignConstraint] = []
        warnings: List[str] = []
        errors: List[str] = []

        for constraint in self._constraints:
            violations = self._validate_single(constraint, design_context)
            constraint.violations = violations

            if not violations:
                passed_count += 1
            else:
                failed.append(constraint)
                if constraint.severity == ConstraintSeverity.FATAL:
                    errors.append(f"[FATAL] {constraint.name}: {violations[0]}")
                elif constraint.severity == ConstraintSeverity.REQUIRED:
                    errors.append(f"[REQUIRED] {constraint.name}: {violations[0]}")
                else:
                    warnings.append(f"[OPTIONAL] {constraint.name}: {violations[0]}")

        result = ConstraintValidationResult(
            passed=len(errors) == 0,
            total=total,
            passed_count=passed_count,
            failed=failed,
            warnings=warnings,
            errors=errors,
        )

        return result

    def suggest_relaxation(
        self, failed_constraints: List[DesignConstraint]
    ) -> List[Dict[str, Any]]:
        """
        Suggest how to relax constraints to make a design valid.

        Returns:
            List of suggestions like:
            {"constraint": "level.min_level", "suggestion": "Reduce min_level from 50 to 30"}
        """
        suggestions = []
        for c in failed_constraints:
            for key, value in c.params.items():
                if isinstance(value, (int, float)):
                    if key.startswith("min_"):
                        suggestions.append(
                            {
                                "constraint": f"{c.category}.{key}",
                                "current": value,
                                "suggestion": f"Reduce {key} from {value} to {value // 2}",
                                "new_value": value // 2,
                            }
                        )
                    elif key.startswith("max_"):
                        suggestions.append(
                            {
                                "constraint": f"{c.category}.{key}",
                                "current": value,
                                "suggestion": f"Increase {key} from {value} to {value + int(value * 0.5)}",
                                "new_value": value + int(value * 0.5),
                            }
                        )
        return suggestions

    def detect_profile_for_map(self, map_data: Dict[str, Any]) -> str:
        """
        Detect which constraint profile best fits a map.

        Analyzes tile count, spawns, towns, and difficulty to recommend a profile.
        """
        tiles = map_data.get("tiles", [])
        spawns = map_data.get("spawns", [])
        towns = map_data.get("towns", [])
        tile_count = len(tiles)

        if not towns and tile_count < 50:
            return "newbie_area"
        if towns and tile_count > 200:
            return "city"
        if any("boss" in str(s).lower() for s in spawns):
            return "boss_room"
        if tile_count > 100 and len(spawns) > 5:
            return "high_end_hunt"
        if spawns:
            return "mid_hunt"

        return "quest_zone"

    # ------------------------------------------------------------------
    # Internal validation
    # ------------------------------------------------------------------

    def _validate_single(
        self, constraint: DesignConstraint, context: Dict[str, Any]
    ) -> List[str]:
        """Validate a single constraint against the design context."""
        violations = []
        params = constraint.params

        for key, value in params.items():
            context_value = context.get(key)

            if context_value is None:
                continue

            if isinstance(value, (int, float)):
                if key.startswith("min_") and context_value < value:
                    violations.append(f"Expected {key} >= {value}, got {context_value}")
                elif key.startswith("max_") and context_value > value:
                    violations.append(f"Expected {key} <= {value}, got {context_value}")

            elif isinstance(value, (list, set, tuple)):
                if isinstance(context_value, str):
                    if context_value not in value:
                        violations.append(
                            f"Expected {key} in {value}, got '{context_value}'"
                        )
                elif isinstance(context_value, (int, float)):
                    if len(value) == 2:
                        lo, hi = value
                        if context_value < lo or context_value > hi:
                            violations.append(
                                f"Expected {key} in [{lo}, {hi}], got {context_value}"
                            )

            elif isinstance(value, bool):
                if value and not context_value:
                    violations.append(f"Expected {key}=True, got {context_value}")

        return violations

    def _extract_constraints_from_profile(
        self, profile: Dict[str, Any], profile_name: str
    ) -> None:
        """Extract DesignConstraint objects from a profile dict."""
        for category, params in profile.items():
            for key, value in params.items():
                severity = (
                    ConstraintSeverity.FATAL
                    if "no_" in key or "min_" in key
                    else ConstraintSeverity.REQUIRED
                )

                constraint = DesignConstraint(
                    name=f"{profile_name}.{category}.{key}",
                    category=category,
                    description=f"{category} constraint: {key}={value}",
                    severity=severity,
                    validator=f"validate_{category}",
                    params={key: value},
                )
                self._constraints.append(constraint)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        cats = self.constraints_by_type()
        return {
            "total_constraints": len(self._constraints),
            "active_profile": self._active_profile,
            "by_category": {k: len(v) for k, v in cats.items()},
            "by_severity": {
                s.value: sum(1 for c in self._constraints if c.severity == s)
                for s in ConstraintSeverity
            },
        }

    def clear(self) -> None:
        self._constraints.clear()
        self._active_profile = None

    @property
    def all_constraints(self) -> List[DesignConstraint]:
        return list(self._constraints)
