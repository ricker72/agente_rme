from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from .goal_engine import GoalEngine, WorldGoal, GoalType
from .constraint_engine import ConstraintEngine, ConstraintValidationResult, DesignConstraint


class DecisionDomain(Enum):
    WHAT = "what"        # qué construir
    WHERE = "where"      # dónde construir
    WHEN = "when"        # cuándo construir


@dataclass
class DesignDecision:
    """
    A concrete design decision made by the Decision Engine.
    """
    domain: DecisionDomain
    what: str
    why: str
    source_goal: Optional[str] = None
    priority: int = 5
    status: str = "pending"  # pending, approved, rejected, executed
    details: Dict[str, Any] = field(default_factory=dict)
    alternatives: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain.value,
            "what": self.what,
            "why": self.why,
            "source_goal": self.source_goal,
            "priority": self.priority,
            "status": self.status,
            "details": self.details,
            "alternatives": self.alternatives,
        }


class DecisionEngine:
    """
    Makes concrete design decisions about what, where, and when to build.

    Decision types:
      - WHAT: Decide which content to create (dungeon, city, boss room, etc.)
      - WHERE: Decide the optimal placement for content
      - WHEN: Decide the order/priority of construction

    Uses GoalEngine for priorities and ConstraintEngine for validation.
    """

    # Priority templates for different content types
    CONTENT_PRIORITIES = {
        "city": 9,
        "temple": 9,
        "depot": 8,
        "boss_room": 8,
        "hunt_zone": 7,
        "quest_zone": 7,
        "market": 6,
        "road": 5,
        "bridge": 5,
        "decoration": 4,
    }

    # Placement rules for WHERE decisions
    PLACEMENT_RULES = {
        "city": {
            "preferred": "center_of_world",
            "distance_from_other_cities": 50,
            "terrain": "flat",
            "adjacent_to": ["road", "water"],
        },
        "temple": {
            "preferred": "center_of_city",
            "distance_from_other_temples": 100,
            "terrain": "flat",
            "adjacent_to": ["depot", "market"],
        },
        "depot": {
            "preferred": "near_temple",
            "distance_from_other_depots": 30,
            "terrain": "flat",
            "adjacent_to": ["temple", "road"],
        },
        "boss_room": {
            "preferred": "end_of_dungeon",
            "distance_from_entrance": 30,
            "terrain": "underground",
            "adjacent_to": ["hunt_zone"],
        },
        "hunt_zone": {
            "preferred": "near_city",
            "distance_from_city": 10,
            "terrain": "mixed",
            "adjacent_to": ["road", "boss_room"],
        },
        "quest_zone": {
            "preferred": "between_cities",
            "distance_from_city": 15,
            "terrain": "underground_or_temple",
            "adjacent_to": ["road", "hunt_zone"],
        },
        "market": {
            "preferred": "city_center",
            "distance_from_depot": 5,
            "terrain": "flat",
            "adjacent_to": ["temple", "depot"],
        },
        "road": {
            "preferred": "connecting_existing",
            "terrain": "any",
            "adjacent_to": ["city", "bridge", "gate"],
        },
        "bridge": {
            "preferred": "over_water",
            "terrain": "water_crossing",
            "adjacent_to": ["road"],
        },
    }

    def __init__(self, goal_engine: Optional[GoalEngine] = None,
                 constraint_engine: Optional[ConstraintEngine] = None):
        self.goal_engine = goal_engine or GoalEngine()
        self.constraint_engine = constraint_engine or ConstraintEngine()
        self._decisions: List[DesignDecision] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def decide_what(self, goals: Optional[List[WorldGoal]] = None) -> List[DesignDecision]:
        """
        Decide WHAT content to create based on active goals.

        Args:
            goals: List of goals. Uses active goals from GoalEngine if None.

        Returns:
            List of DesignDecision objects for each content piece to create.
        """
        if goals is None:
            goals = self.goal_engine.get_pending_goals()
            if not goals:
                goals = self.goal_engine.get_active_goals()

        decisions: List[DesignDecision] = []

        for goal in goals:
            content_decisions = self._goal_to_decisions(goal)
            decisions.extend(content_decisions)

        # Sort by priority
        decisions.sort(key=lambda d: d.priority, reverse=True)
        self._decisions.extend(decisions)

        return decisions

    def decide_where(self, decision: DesignDecision,
                     world_context: Dict[str, Any]) -> DesignDecision:
        """
        Decide WHERE to place a piece of content.

        Args:
            decision: The WHAT decision.
            world_context: Dict with existing map data:
                - "existing_cities": list of positions
                - "existing_zones": list of zone positions
                - "width", "height": world bounds
                - "terrain_map": terrain type per coordinate

        Returns:
            The updated DesignDecision with position details.
        """
        content_type = self._extract_content_type(decision)
        rules = self.PLACEMENT_RULES.get(content_type, {})

        position = self._find_optimal_position(content_type, rules, world_context)
        decision.details["position"] = position
        decision.details["rules_applied"] = rules
        decision.domain = DecisionDomain.WHERE
        decision.why = f"Placed at {position} following {content_type} placement rules"

        return decision

    def decide_when(self, decisions: List[DesignDecision]) -> List[DesignDecision]:
        """
        Decide WHEN (in what order) to execute decisions.

        Args:
            decisions: List of WHAT decisions.

        Returns:
            Sorted list of decisions in execution order.
        """
        sorted_decisions = sorted(
            decisions,
            key=lambda d: (
                d.priority * -1,                                          # Priority descending
                0 if d.details.get("position") else 1,                   # Positioned first
                len(self._find_dependencies(d, decisions)) * -1,         # Most dependents first
            )
        )

        for i, d in enumerate(sorted_decisions):
            d.details["execution_order"] = i + 1
            d.details["phase"] = self._assign_phase(i, len(sorted_decisions))

        self._decisions = sorted_decisions
        return sorted_decisions

    def evaluate_decision(self, decision: DesignDecision,
                          design_context: Dict[str, Any]) -> ConstraintValidationResult:
        """
        Evaluate a decision against design constraints.

        Args:
            decision: The decision to evaluate.
            design_context: Context dict for constraint validation.

        Returns:
            ConstraintValidationResult with pass/fail.
        """
        content_type = self._extract_content_type(decision)
        profile = self.constraint_engine.detect_profile_for_map(design_context)
        self.constraint_engine.load_profile(profile)

        return self.constraint_engine.validate(design_context)

    def approve_decision(self, decision: DesignDecision) -> None:
        """Approve a decision for execution."""
        decision.status = "approved"

    def reject_decision(self, decision: DesignDecision, reason: str) -> None:
        """Reject a decision with a reason."""
        decision.status = "rejected"
        decision.why = f"REJECTED: {reason}"

    def get_decisions(self, status: Optional[str] = None,
                      domain: Optional[DecisionDomain] = None) -> List[DesignDecision]:
        """Get all decisions, optionally filtered."""
        results = list(self._decisions)
        if status:
            results = [d for d in results if d.status == status]
        if domain:
            results = [d for d in results if d.domain == domain]
        return results

    def get_pending(self) -> List[DesignDecision]:
        return self.get_decisions("pending")

    def get_approved(self) -> List[DesignDecision]:
        return self.get_decisions("approved")

    def get_executed(self) -> List[DesignDecision]:
        return self.get_decisions("executed")

    # ------------------------------------------------------------------
    # Goal → Decision conversion
    # ------------------------------------------------------------------

    def _goal_to_decisions(self, goal: WorldGoal) -> List[DesignDecision]:
        """Convert a WorldGoal into specific design decisions."""
        decisions: List[DesignDecision] = []

        if goal.goal_type == GoalType.EXPAND_WORLD:
            count = goal.targets.get("new_areas", 1)
            for i in range(count):
                decisions.append(DesignDecision(
                    domain=DecisionDomain.WHAT,
                    what=f"New area {i + 1}",
                    why=f"Required by goal: {goal.name}",
                    source_goal=goal.name,
                    priority=goal.priority,
                    details={"target": "expansion", "index": i},
                    alternatives=["No expansion", "Smaller area"],
                ))

        elif goal.goal_type == GoalType.ADD_CONTENT:
            for content_type, count in goal.targets.items():
                for i in range(count):
                    decisions.append(DesignDecision(
                        domain=DecisionDomain.WHAT,
                        what=f"{content_type} {i + 1}",
                        why=f"Content addition from goal: {goal.name}",
                        source_goal=goal.name,
                        priority=self.CONTENT_PRIORITIES.get(content_type, 5),
                        details={"content_type": content_type, "index": i},
                    ))

        elif goal.goal_type == GoalType.ADD_ENDGAME:
            bosses = goal.targets.get("bosses", 3)
            hunts = goal.targets.get("hunts_high", 3)
            for i in range(bosses):
                decisions.append(DesignDecision(
                    domain=DecisionDomain.WHAT,
                    what=f"Boss room {i + 1}",
                    why=f"Endgame boss from: {goal.name}",
                    source_goal=goal.name,
                    priority=9,
                    details={"content_type": "boss_room", "difficulty": "high"},
                ))
            for i in range(hunts):
                decisions.append(DesignDecision(
                    domain=DecisionDomain.WHAT,
                    what=f"High level hunt {i + 1}",
                    why=f"Endgame hunt from: {goal.name}",
                    source_goal=goal.name,
                    priority=8,
                    details={"content_type": "hunt_zone", "difficulty": "high"},
                ))

        elif goal.goal_type == GoalType.FIX_QUALITY:
            decisions.append(DesignDecision(
                domain=DecisionDomain.WHAT,
                what="Quality improvement pass",
                why=f"Quality fix from: {goal.name}",
                source_goal=goal.name,
                priority=6,
                details={"action": "improve_quality", "target_score": goal.targets.get("min_score", 85)},
            ))

        elif goal.goal_type == GoalType.ADD_QUESTS:
            zones = goal.targets.get("quest_zones", 3)
            for i in range(zones):
                decisions.append(DesignDecision(
                    domain=DecisionDomain.WHAT,
                    what=f"Quest zone {i + 1}",
                    why=f"Quest content from: {goal.name}",
                    source_goal=goal.name,
                    priority=7,
                    details={"content_type": "quest_zone", "chests": goal.targets.get("chests", 5)},
                ))

        else:
            decisions.append(DesignDecision(
                domain=DecisionDomain.WHAT,
                what=f"Content for: {goal.name}",
                why=f"Generated from goal: {goal.name}",
                source_goal=goal.name,
                priority=goal.priority,
                details={"goal_type": goal.goal_type.value},
            ))

        return decisions

    # ------------------------------------------------------------------
    # Position finding
    # ------------------------------------------------------------------

    def _find_optimal_position(self, content_type: str, rules: Dict[str, Any],
                                world_context: Dict[str, Any]) -> Dict[str, Any]:
        """Find the optimal position for a content type given rules and context."""
        existing_cities = world_context.get("existing_cities", [])
        existing_zones = world_context.get("existing_zones", [])
        width = world_context.get("width", 100)
        height = world_context.get("height", 100)

        preferred = rules.get("preferred", "center")
        position = {"x": width // 2, "y": height // 2, "z": 7}

        if preferred == "center_of_world":
            position = {"x": width // 2, "y": height // 2, "z": 7}
        elif preferred == "center_of_city" and existing_cities:
            pos = existing_cities[0]
            position = {"x": pos.get("x", 50) + 5, "y": pos.get("y", 50), "z": 7}
        elif preferred == "near_temple" and existing_cities:
            pos = existing_cities[0]
            position = {"x": pos.get("x", 50) + 3, "y": pos.get("y", 50) + 3, "z": 7}
        elif preferred == "end_of_dungeon":
            position = {"x": width - 15, "y": height - 15, "z": 7}
        elif preferred == "near_city" and existing_cities:
            pos = existing_cities[0]
            distance = rules.get("distance_from_city", 10)
            position = {"x": pos.get("x", 50) + distance, "y": pos.get("y", 50), "z": 7}
        elif preferred == "connecting_existing" and existing_zones:
            first = existing_zones[0]
            last = existing_zones[-1]
            position = {
                "x": (first.get("x", 0) + last.get("x", width)) // 2,
                "y": (first.get("y", 0) + last.get("y", height)) // 2,
                "z": 7,
            }
        elif preferred == "over_water":
            position = {"x": width // 2, "y": 0, "z": 7, "over_water": True}

        position["content_type"] = content_type
        position["preferred"] = preferred

        return position

    def _extract_content_type(self, decision: DesignDecision) -> str:
        """Extract the content type from a decision."""
        # Check details first
        ct = decision.details.get("content_type")
        if ct:
            return ct

        # Check decision.what keywords
        lower = decision.what.lower()
        for content_type in self.CONTENT_PRIORITIES:
            if content_type in lower:
                return content_type

        return "unknown"

    # ------------------------------------------------------------------
    # Ordering
    # ------------------------------------------------------------------

    def _find_dependencies(self, decision: DesignDecision,
                           all_decisions: List[DesignDecision]) -> List[DesignDecision]:
        """Find decisions that depend on this one."""
        content_type = self._extract_content_type(decision)
        dependents = []

        for other in all_decisions:
            if other is decision:
                continue
            rules = self.PLACEMENT_RULES.get(self._extract_content_type(other), {})
            adjacent_to = rules.get("adjacent_to", [])
            if content_type in adjacent_to:
                dependents.append(other)

        return dependents

    def _assign_phase(self, index: int, total: int) -> str:
        """Assign a build phase based on execution index."""
        if total <= 3:
            return "single"
        if index < total * 0.33:
            return "phase_1"
        elif index < total * 0.66:
            return "phase_2"
        return "phase_3"

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        status_counts = {"pending": 0, "approved": 0, "rejected": 0, "executed": 0}
        for d in self._decisions:
            status_counts[d.status] = status_counts.get(d.status, 0) + 1

        return {
            "total_decisions": len(self._decisions),
            "status_counts": status_counts,
            "decisions_by_domain": {
                dd.value: sum(1 for d in self._decisions if d.domain == dd)
                for dd in DecisionDomain
            },
        }

    def clear(self) -> None:
        self._decisions.clear()