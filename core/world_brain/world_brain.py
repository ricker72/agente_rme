from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .goal_engine import GoalEngine, WorldGoal, GoalType
from .constraint_engine import ConstraintEngine, ConstraintValidationResult, DesignConstraint
from .decision_engine import DecisionEngine, DesignDecision, DecisionDomain
from .reasoning_engine import ReasoningEngine, DesignExplanation


@dataclass
class WorldBrainState:
    """
    Current state of the World Brain's cognitive process.
    """
    is_thinking: bool = False
    current_goal: Optional[str] = None
    decisions_made: int = 0
    decisions_executed: int = 0
    explanations_given: int = 0
    constraints_validated: int = 0
    iteration: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_thinking": self.is_thinking,
            "current_goal": self.current_goal,
            "decisions_made": self.decisions_made,
            "decisions_executed": self.decisions_executed,
            "explanations_given": self.explanations_given,
            "constraints_validated": self.constraints_validated,
            "iteration": self.iteration,
        }


@dataclass
class BrainSession:
    """
    Complete record of a World Brain thinking session.
    """
    prompt: str
    goals: List[WorldGoal] = field(default_factory=list)
    decisions: List[DesignDecision] = field(default_factory=list)
    explanations: List[DesignExplanation] = field(default_factory=list)
    constraints_result: Optional[ConstraintValidationResult] = None
    success: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt": self.prompt,
            "goals": [g.to_dict() for g in self.goals],
            "decisions": [d.to_dict() for d in self.decisions],
            "explanations": [e.to_dict() for e in self.explanations],
            "constraints_passed": self.constraints_result.passed if self.constraints_result else None,
            "success": self.success,
        }


class WorldBrain:
    """
    Central cognitive system for the RME.

    The WorldBrain is the master orchestrator that:

    1. Takes a design goal (from prompt or auto-detection)
    2. Decomposes it into sub-goals (GoalEngine)
    3. Validates against constraints (ConstraintEngine)
    4. Makes design decisions (DecisionEngine)
    5. Explains rationale (ReasoningEngine)
    6. Passes decisions to generation pipeline

    Pipeline:
        Prompt → GoalEngine → ConstraintEngine → DecisionEngine
        → ReasoningEngine → Execution

    Unlike previous systems that reacted to prompts, WorldBrain
    proactively makes design decisions based on world context.
    """

    def __init__(self):
        self.goal_engine = GoalEngine()
        self.constraint_engine = ConstraintEngine()
        self.decision_engine = DecisionEngine(self.goal_engine, self.constraint_engine)
        self.reasoning_engine = ReasoningEngine()
        self.state = WorldBrainState()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def think(self, prompt: str, world_context: Optional[Dict[str, Any]] = None) -> BrainSession:
        """
        The main cognitive entry point.

        Given a design goal (e.g., "Crear expansión endgame"),
        this method will think through all aspects of the design
        and produce a complete session with goals, decisions, and rationale.

        Args:
            prompt: Natural language design prompt.
            world_context: Dict with existing world data for context.

        Returns:
            BrainSession with all decisions and rationale.
        """
        self.state.is_thinking = True
        self.state.iteration += 1
        self.state.current_goal = prompt[:60]

        session = BrainSession(prompt=prompt)
        wc = world_context or {}

        # Step 1: Parse goals
        goals = self.goal_engine.create_goals_from_prompt(prompt)
        session.goals = goals
        self.state.current_goal = goals[0].name if goals else prompt[:60]

        # Step 2: Decompose and prioritize
        all_goals = list(goals)
        for goal in goals:
            sub_goals = self.goal_engine.decompose_goal(goal)
            for sg in sub_goals:
                if sg is not goal:  # Only add new sub-goals
                    all_goals.append(sg)

        # Step 3: Make decisions from goals
        decisions = self.decision_engine.decide_what(all_goals)

        # Step 4: Apply WHERE decisions
        for decision in decisions:
            self.decision_engine.decide_where(decision, wc)

        # Step 5: Order decisions (WHEN)
        ordered = self.decision_engine.decide_when(decisions)
        session.decisions = ordered

        # Step 6: Validate constraints
        for decision in ordered:
            validation = self.decision_engine.evaluate_decision(decision, wc)
            if validation.passed:
                self.decision_engine.approve_decision(decision)
            else:
                self.decision_engine.reject_decision(
                    decision,
                    f"Constraints failed: {', '.join(validation.errors)}"
                )
            session.constraints_result = validation
            self.state.constraints_validated += 1

        # Step 7: Generate explanations
        for decision in ordered:
            question = f"Por que {decision.what.lower()}?"
            explanation = self.reasoning_engine.explain(question)
            self.reasoning_engine.register_decision(decision.what, explanation)
            session.explanations.append(explanation)
            self.state.explanations_given += 1

        # Step 8: Log decision rationale
        for decision in ordered:
            self.reasoning_engine.log_decision(
                what=decision.what,
                why=decision.why,
                context={"source_goal": decision.source_goal, "priority": decision.priority},
            )

        self.state.decisions_made = len(ordered)
        self.state.decisions_executed = len([d for d in ordered if d.status == "executed"])
        session.success = all(d.status == "approved" for d in ordered if d.priority > 7)
        self.state.is_thinking = False

        return session

    def answer_why(self, question: str) -> DesignExplanation:
        """
        Answer a "why" question about the current design.

        Delegates to ReasoningEngine with full context from the session.
        """
        self.state.explanations_given += 1
        return self.reasoning_engine.explain(question)

    def get_state(self) -> WorldBrainState:
        """Get the current cognitive state."""
        return self.state

    def get_decision_log(self) -> List[Dict[str, Any]]:
        """Get the full decision audit log."""
        return self.reasoning_engine.get_decision_log()

    def reframe(self, prompt: str, world_context: Optional[Dict[str, Any]] = None) -> BrainSession:
        """
        Re-think with a new perspective while preserving previous decisions.

        Like think() but builds upon existing goals and decisions.
        """
        self.state.iteration += 1
        previous_count = len(self.goal_engine.all_goals)

        # Create additional goals from the new prompt
        new_goals = self.goal_engine.create_goals_from_prompt(prompt)

        # Re-run the thinking process with combined goals
        combined_prompt = f"{self.state.current_goal or ''} + {prompt}"
        session = self.think(combined_prompt, world_context)

        session.goals = self.goal_engine.all_goals  # Include all goals (old + new)

        return session

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        """Comprehensive brain status."""
        return {
            "state": self.state.to_dict(),
            "goals": self.goal_engine.summary(),
            "constraints": self.constraint_engine.summary(),
            "decisions": self.decision_engine.summary(),
            "reasoning": self.reasoning_engine.audit_summary(),
        }

    def clear(self) -> None:
        """Reset the brain's cognitive state."""
        self.goal_engine.clear()
        self.constraint_engine.clear()
        self.decision_engine.clear()
        self.reasoning_engine.clear()
        self.state = WorldBrainState()