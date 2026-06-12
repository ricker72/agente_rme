from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class GoalType(Enum):
    EXPAND_WORLD = "expand_world"
    ADD_CONTENT = "add_content"
    FIX_QUALITY = "fix_quality"
    BALANCE_GAMEPLAY = "balance_gameplay"
    ADD_ENDGAME = "add_endgame"
    ADD_QUESTS = "add_quests"
    MODERNIZE = "modernize"
    NATURALIZE = "naturalize"


@dataclass
class WorldGoal:
    """
    A high-level design goal with quantified targets.

    Example:
        WorldGoal(
            goal_type=GoalType.EXPAND_WORLD,
            name="Crear expansión endgame",
            priority=9,
            targets={"cities": 2, "hunts": 5, "bosses": 8, "quests": 20}
        )
    """

    goal_type: GoalType
    name: str
    priority: int = 5  # 1-10
    description: str = ""
    targets: Dict[str, int] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, active, completed, blocked
    progress: float = 0.0  # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_type": self.goal_type.value,
            "name": self.name,
            "priority": self.priority,
            "description": self.description,
            "targets": self.targets,
            "constraints": self.constraints,
            "dependencies": self.dependencies,
            "status": self.status,
            "progress": self.progress,
        }


class GoalEngine:
    """
    Defines and manages high-level world design goals.

    A goal translates abstract intent (e.g., "Crear expansión endgame")
    into quantified targets with constraints.

    Capabilities:
      - Parse natural language goals into structured targets
      - Decompose complex goals into sub-goals
      - Track progress across multiple goals
      - Check dependencies between goals
      - Prioritize goals based on map needs
    """

    # Common target templates for different goal types
    GOAL_TEMPLATES = {
        GoalType.EXPAND_WORLD: {
            "description": "Expandir el mundo con nuevas zonas jugables",
            "targets": {"new_areas": 1, "zones": 5},
            "constraints": {"min_area_size": 100, "max_area_size": 500},
        },
        GoalType.ADD_CONTENT: {
            "description": "Añadir contenido nuevo: hunts, bosses, quests",
            "targets": {"hunts": 2, "boss_rooms": 1, "quest_zones": 1},
            "constraints": {"min_spawns_per_hunt": 3, "boss_min_level": 100},
        },
        GoalType.FIX_QUALITY: {
            "description": "Mejorar la calidad del mapa existente",
            "targets": {"min_score": 85},
            "constraints": {"connectivity_min": 0.7, "decoration_min": 15},
        },
        GoalType.BALANCE_GAMEPLAY: {
            "description": "Balancear la dificultad y distribución de contenido",
            "targets": {"score_balance": 20},
            "constraints": {
                "spawn_density_range": (0.3, 0.7),
                "level_range": (50, 300),
            },
        },
        GoalType.ADD_ENDGAME: {
            "description": "Crear contenido de alto nivel para jugadores avanzados",
            "targets": {"bosses": 3, "hunts_high": 3, "quests_epic": 2},
            "constraints": {"min_level": 200, "boss_min_level": 300},
        },
        GoalType.ADD_QUESTS: {
            "description": "Añadir zonas de quest con recompensas y progresión",
            "targets": {"quest_zones": 3, "chests": 5, "npcs": 2},
            "constraints": {"chest_count_per_zone": 1},
        },
        GoalType.MODERNIZE: {
            "description": "Actualizar items, monstruos y formato a versión moderna",
            "targets": {"items_updated": 50, "monsters_normalized": 20},
            "constraints": {"target_version": "14.x"},
        },
        GoalType.NATURALIZE: {
            "description": "Mejorar la estética natural del mapa",
            "targets": {"decoration_density": 20},
            "constraints": {"ground_variety": 4, "min_decor_per_100": 15},
        },
    }

    def __init__(self):
        self._goals: List[WorldGoal] = []
        self._active_goal: Optional[WorldGoal] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_goal(
        self,
        name: str,
        goal_type: Optional[GoalType] = None,
        priority: int = 5,
        targets: Optional[Dict[str, int]] = None,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> WorldGoal:
        """
        Create a new world goal.

        Args:
            name: Human-readable goal name.
            goal_type: Type of goal. Auto-detected if None.
            priority: 1-10 priority level.
            targets: Quantified targets. Auto-filled from template if None.
            constraints: Design constraints. Auto-filled from template if None.

        Returns:
            The created WorldGoal.
        """
        if goal_type is None:
            goal_type = self._detect_goal_type(name)

        template = self.GOAL_TEMPLATES.get(goal_type, {})
        goal = WorldGoal(
            goal_type=goal_type,
            name=name,
            priority=priority,
            description=template.get("description", name),
            targets=targets or dict(template.get("targets", {})),
            constraints=constraints or dict(template.get("constraints", {})),
            status="pending",
        )

        self._goals.append(goal)
        return goal

    def create_goals_from_prompt(self, prompt: str) -> List[WorldGoal]:
        """
        Parse a natural language prompt into one or more goals.

        Example:
            "Crear expansión endgame con ciudades y hunts"
            → [EXPAND_WORLD, ADD_ENDGAME, ADD_CONTENT]
        """
        lower = prompt.lower()
        goals: List[WorldGoal] = []

        if "expans" in lower or "nuev" in lower:
            goals.append(
                self.create_goal(
                    f"Expand world: {prompt[:40]}",
                    GoalType.EXPAND_WORLD,
                    priority=8,
                )
            )

        if "endgame" in lower or "boss" in lower or "end game" in lower:
            goals.append(
                self.create_goal(
                    f"Add endgame content: {prompt[:40]}",
                    GoalType.ADD_ENDGAME,
                    priority=9,
                )
            )

        if "quest" in lower or "mision" in lower or "misi" in lower:
            goals.append(
                self.create_goal(
                    f"Add quests: {prompt[:40]}",
                    GoalType.ADD_QUESTS,
                    priority=7,
                )
            )

        if "calidad" in lower or "quality" in lower or "mejor" in lower:
            goals.append(
                self.create_goal(
                    f"Fix quality: {prompt[:40]}",
                    GoalType.FIX_QUALITY,
                    priority=6,
                )
            )

        if "balance" in lower or "balancear" in lower:
            goals.append(
                self.create_goal(
                    f"Balance gameplay: {prompt[:40]}",
                    GoalType.BALANCE_GAMEPLAY,
                    priority=6,
                )
            )

        if not goals:
            goals.append(
                self.create_goal(
                    prompt,
                    priority=5,
                )
            )

        return goals

    def set_active_goal(self, goal: WorldGoal) -> None:
        """Set a goal as the currently active focus."""
        self._active_goal = goal
        goal.status = "active"

    def get_active_goal(self) -> Optional[WorldGoal]:
        return self._active_goal

    def get_goals(self, status: Optional[str] = None) -> List[WorldGoal]:
        """Get all goals, optionally filtered by status."""
        if status:
            return [g for g in self._goals if g.status == status]
        return list(self._goals)

    def get_pending_goals(self) -> List[WorldGoal]:
        return self.get_goals("pending")

    def get_active_goals(self) -> List[WorldGoal]:
        return self.get_goals("active")

    def mark_completed(self, goal: WorldGoal) -> None:
        """Mark a goal as completed."""
        goal.status = "completed"
        goal.progress = 1.0

    def mark_blocked(self, goal: WorldGoal, reason: str) -> None:
        """Mark a goal as blocked due to unmet dependencies."""
        goal.status = "blocked"
        goal.description = f"{goal.description} [BLOCKED: {reason}]"

    def update_progress(self, goal: WorldGoal, progress: float) -> None:
        """Update goal progress (0.0 to 1.0)."""
        goal.progress = max(0.0, min(1.0, progress))
        if goal.progress >= 1.0:
            goal.status = "completed"

    def prioritize(self) -> List[WorldGoal]:
        """
        Sort all pending goals by priority (highest first).

        Returns:
            Sorted list of pending goals.
        """
        pending = [g for g in self._goals if g.status == "pending"]
        pending.sort(key=lambda g: g.priority, reverse=True)

        # Check dependencies
        goal_names = {g.name for g in self._goals}
        for goal in pending:
            for dep in goal.dependencies:
                if dep not in goal_names:
                    self.mark_blocked(goal, f"Dependency '{dep}' not found")

        return [g for g in pending if g.status == "pending"]

    def next_goal(self) -> Optional[WorldGoal]:
        """Get the next highest-priority unblocked goal."""
        pending = self.prioritize()
        if pending:
            goal = pending[0]
            self.set_active_goal(goal)
            return goal
        return None

    def decompose_goal(self, goal: WorldGoal) -> List[WorldGoal]:
        """
        Decompose a complex goal into sub-goals.

        Example:
            "Crear expansión endgame"
            → [Create city, Create hunt zone, Create boss room, Create quest zone]
        """
        sub_goals: List[WorldGoal] = []

        if goal.goal_type == GoalType.EXPAND_WORLD:
            sub_goals.append(
                self.create_goal(
                    "Add city district",
                    GoalType.EXPAND_WORLD,
                    priority=6,
                    targets={"cities": 1},
                )
            )
            sub_goals.append(
                self.create_goal(
                    "Add hunting grounds",
                    GoalType.ADD_CONTENT,
                    priority=7,
                    targets={"hunts": 2},
                )
            )

        elif goal.goal_type == GoalType.ADD_ENDGAME:
            sub_goals.append(
                self.create_goal(
                    "Add boss rooms",
                    GoalType.ADD_CONTENT,
                    priority=9,
                    targets={"boss_rooms": goal.targets.get("bosses", 3)},
                )
            )
            sub_goals.append(
                self.create_goal(
                    "Add high-level hunts",
                    GoalType.ADD_CONTENT,
                    priority=8,
                    targets={"hunts": goal.targets.get("hunts_high", 3)},
                )
            )

        if not sub_goals:
            return [goal]  # Can't decompose further

        for sub in sub_goals:
            sub.dependencies.append(goal.name)

        return sub_goals

    # ------------------------------------------------------------------
    # Query parsing
    # ------------------------------------------------------------------

    def _detect_goal_type(self, name: str) -> GoalType:
        """Auto-detect goal type from a name string."""
        lower = name.lower()
        if any(kw in lower for kw in ["expans", "nuev", "new area", "add area"]):
            return GoalType.EXPAND_WORLD
        if any(kw in lower for kw in ["content", "monster", "spawn", "hunt"]):
            return GoalType.ADD_CONTENT
        if any(kw in lower for kw in ["quality", "calidad", "fix", "repair"]):
            return GoalType.FIX_QUALITY
        if any(kw in lower for kw in ["balance", "balancear"]):
            return GoalType.BALANCE_GAMEPLAY
        if any(kw in lower for kw in ["endgame", "end game", "boss", "high level"]):
            return GoalType.ADD_ENDGAME
        if any(kw in lower for kw in ["quest", "quests", "mision", "misi"]):
            return GoalType.ADD_QUESTS
        if any(kw in lower for kw in ["modernize", "modernizar", "update", "version"]):
            return GoalType.MODERNIZE
        if any(kw in lower for kw in ["nature", "natural", "decor", "estet"]):
            return GoalType.NATURALIZE
        return GoalType.ADD_CONTENT

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        status_counts = {"pending": 0, "active": 0, "completed": 0, "blocked": 0}
        for g in self._goals:
            status_counts[g.status] = status_counts.get(g.status, 0) + 1

        return {
            "total_goals": len(self._goals),
            "status_counts": status_counts,
            "active_goal": self._active_goal.name if self._active_goal else None,
            "goals_by_type": {
                gt.value: sum(1 for g in self._goals if g.goal_type == gt)
                for gt in GoalType
            },
        }

    @property
    def all_goals(self) -> List[WorldGoal]:
        return list(self._goals)

    def clear(self) -> None:
        self._goals.clear()
        self._active_goal = None

    def __len__(self) -> int:
        return len(self._goals)
