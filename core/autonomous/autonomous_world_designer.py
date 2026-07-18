"""
Autonomous World Designer — main façade for autonomous world generation.

This is the public entry point used by the CLI and the integration tests.
It composes all the autonomous modules (Director, Planner, Decision Engine,
Optimizer, Goal Manager) and wires the real subsystems (Knowledge,
Blueprint Intelligence, Visual Critic, Playtest, Balance, Evolution, OTBM
exporter) into a single end-to-end pipeline.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models.design_goal import DesignGoal
from .models.design_result import DesignResult
from .autonomous_director import AutonomousDirector
from .autonomous_planner import AutonomousPlanner
from .autonomous_decision_engine import AutonomousDecisionEngine
from .autonomous_optimizer import AutonomousOptimizer
from .goal_manager import GoalManager

logger = logging.getLogger(__name__)


# ── Lazy subsystem imports (kept optional for testability) ──────────────────
def _try_load(cls_path: str):
    try:
        module_path, cls_name = cls_path.rsplit(".", 1)
        import importlib

        module = importlib.import_module(module_path)
        return getattr(module, cls_name, None)
    except Exception:  # pragma: no cover - defensive
        return None


@dataclass
class AutonomousWorldDesigner:
    """Main façade for autonomous world generation."""

    director: AutonomousDirector = field(default_factory=AutonomousDirector)
    planner: AutonomousPlanner = field(default_factory=AutonomousPlanner)
    decision_engine: AutonomousDecisionEngine = field(
        default_factory=AutonomousDecisionEngine
    )
    optimizer: AutonomousOptimizer = field(default_factory=AutonomousOptimizer)
    goal_manager: GoalManager = field(default_factory=GoalManager)

    history: List[Dict[str, Any]] = field(default_factory=list)
    output_dir: str = "output/autonomous"

    # Optional wiring (filled by ``wire_subsystems``)
    knowledge_engine: Any = None
    blueprint_intelligence: Any = None
    visual_critic: Any = None

    def __post_init__(self) -> None:
        os.makedirs(self.output_dir, exist_ok=True)
        # Wire the planner's director with our director so they share state
        if self.planner.director is not self.director:
            self.planner.director = self.director
        # If a critic was passed, share it with the optimizer
        if self.visual_critic is not None and self.optimizer.visual_critic is None:
            self.optimizer.visual_critic = self.visual_critic

    # ------------------------------------------------------------------ public

    def wire_subsystems(
        self,
        knowledge_engine: Any = None,
        blueprint_intelligence: Any = None,
        visual_critic: Any = None,
    ) -> "AutonomousWorldDesigner":
        """Inject the real subsystems so the autonomous modules can consume them."""
        if knowledge_engine is not None:
            self.knowledge_engine = knowledge_engine
            self.director.knowledge_engine = knowledge_engine
            self.decision_engine.knowledge_engine = knowledge_engine
        if blueprint_intelligence is not None:
            self.blueprint_intelligence = blueprint_intelligence
            self.director.blueprint_intelligence = blueprint_intelligence
            self.decision_engine.blueprint_intelligence = blueprint_intelligence
        if visual_critic is not None:
            self.visual_critic = visual_critic
            self.optimizer.visual_critic = visual_critic
        return self

    def generate(self, prompt: str, max_iterations: int = 20) -> DesignResult:
        """Generate a world from a natural language prompt."""
        # Lazy subsystem loading if not wired explicitly
        self._lazy_load_subsystems()

        goal = self.director.parse_prompt(prompt)
        plan = self.planner.create_plan(goal)
        # Let the decision engine pick blueprints for each region
        self._populate_plan_with_decisions(plan, goal)

        self.optimizer.max_iterations = max_iterations
        result = self.optimizer.run_optimization(plan, goal)

        # Optionally export the final world
        result.final_world = self._build_final_world(plan)
        self._export_world_if_possible(result, plan)

        self._record_generation(prompt, result)
        self._export_results(result)

        return result

    def optimize(self, prompt: str, max_iterations: int = 20) -> DesignResult:
        """Optimize an existing world design (alias of ``generate``)."""
        return self.generate(prompt, max_iterations)

    def benchmark(self, num_worlds: int = 50) -> Dict[str, Any]:
        """Run a benchmark by generating multiple worlds and aggregating metrics."""
        self._lazy_load_subsystems()
        start = time.time()
        results: List[DesignResult] = []
        for i in range(num_worlds):
            prompt = (
                f"Test world {i + 1} | level {100 + (i % 5) * 50}-{150 + (i % 5) * 50} | "
                f"hunts {1 + (i % 3)} bosses {(i % 2)}"
            )
            try:
                result = self.generate(prompt, max_iterations=3)
            except Exception as exc:
                logger.debug("benchmark world %d failed: %s", i, exc)
                continue
            results.append(result)

        successful = [r for r in results if r.success]
        scores = [r.final_scores.get("critic", 0) for r in results]
        improvement = []
        for r in results:
            if len(r.convergence_data) > 1:
                improvement.append(r.convergence_data[-1] - r.convergence_data[0])

        report = {
            "total_worlds": len(results),
            "successful_worlds": len(successful),
            "success_rate": (len(successful) / len(results)) if results else 0.0,
            "average_score": (sum(scores) / len(scores)) if scores else 0.0,
            "max_score": max(scores) if scores else 0.0,
            "min_score": min(scores) if scores else 0.0,
            "average_improvement": (sum(improvement) / len(improvement))
            if improvement
            else 0.0,
            "converged_worlds": sum(
                1
                for r in results
                if len(r.convergence_data) > 1
                and abs(r.convergence_data[-1] - r.convergence_data[-2]) < 0.1
            ),
            "total_duration_seconds": time.time() - start,
            "timestamp": datetime.now().isoformat(),
        }

        self._export_benchmark(report)
        return report

    def report(self) -> Dict[str, Any]:
        return {
            "total_generations": len(self.history),
            "history": self.history[-10:],
            "decision_stats": self.decision_engine.get_decision_stats(),
            "optimization_stats": self.optimizer.get_optimization_stats(),
            "memory_stats": self.director.get_memory_stats(),
        }

    # ------------------------------------------------------------------ internal

    def _populate_plan_with_decisions(self, plan: Any, goal: DesignGoal) -> None:
        """Let the DecisionEngine pick blueprints, patterns and clusters for every region."""
        for region in plan.regions:
            try:
                bp_decision = self.decision_engine.select_blueprint(region)
                region.selected_blueprints = [bp_decision.selected_option]
            except Exception as exc:
                logger.debug("blueprint decision failed: %s", exc)
                region.selected_blueprints = [f"blueprint_{region.region_type}_1"]

            try:
                pat_decision = self.decision_engine.select_pattern(region)
                region.patterns = [pat_decision.selected_option]
            except Exception as exc:
                logger.debug("pattern decision failed: %s", exc)
                region.patterns = [f"pattern_{region.region_type}_{region.region_id}"]

            # Record these decisions in the director memory for the report
            self.director.record_decision(
                "blueprint",
                region.region_id,
                region.selected_blueprints[0],
                0.85,
                metadata={"region_type": region.region_type},
            )
            self.director.record_decision(
                "pattern",
                region.region_id,
                region.patterns[0],
                0.8,
                metadata={"region_type": region.region_type},
            )

    def _build_final_world(self, plan: Any) -> Optional[Any]:
        """Return a deterministic world representation for the plan."""
        try:
            from core.world.world_model import WorldModel  # type: ignore
            from core.world.tile import Tile  # type: ignore
            from core.world.region import Region  # type: ignore
            from core.world.structure import Structure  # type: ignore
            from core.world.spawn import Spawn  # type: ignore
        except Exception:  # pragma: no cover
            return None

        world = WorldModel()
        cursor_x = 0
        for region in plan.regions:
            width = max(1, int(region.target_size**0.5))
            height = max(1, int((region.target_size / max(1, width))))
            for dx in range(width):
                for dy in range(height):
                    tile = Tile(
                        x=cursor_x + dx,
                        y=dy,
                        z=7,
                        ground=200 + (hash(region.region_id) % 50),
                        zone=region.region_id,
                    )
                    if (
                        region.region_type in ("hunt", "raid", "boss")
                        and (dx + dy) % 4 == 0
                    ):
                        try:
                            tile.spawn = Spawn(monster="Demon", respawn=60, radius=2)
                        except Exception:
                            pass
                    if region.region_type == "city" and (dx + dy) % 2 == 0:
                        tile.items = [{"itemid": 200 + (dx + dy) % 10, "count": 1}]
                    world.set_tile(tile)
            try:
                world.add_region(
                    Region(
                        name=region.region_id,
                        theme=region.region_name,
                        min_level=region.level_range[0],
                        max_level=region.level_range[1],
                    )
                )
            except Exception:
                pass
            if region.region_type in ("boss", "raid", "city"):
                try:
                    world.add_structure(
                        Structure(
                            name=f"struct_{region.region_id}",
                            category=region.region_type,
                            x=cursor_x,
                            y=0,
                            z=7,
                            width=width,
                            height=height,
                            tags=[region.region_type],
                        )
                    )
                except Exception:
                    pass
            cursor_x += width + 4
        return world

    def _export_world_if_possible(self, result: DesignResult, plan: Any) -> None:
        if self.optimizer.otbm_exporter is None or result.final_world is None:
            return
        try:
            otbm_path = os.path.join(self.output_dir, f"{result.result_id}.otbm")
            self.optimizer.otbm_exporter.export(result.final_world, otbm_path)
        except Exception as exc:
            logger.debug("OTBM export failed: %s", exc)

    def _record_generation(self, prompt: str, result: DesignResult) -> None:
        self.history.append(
            {
                "prompt": prompt,
                "result_id": result.result_id,
                "success": result.success,
                "final_scores": result.final_scores,
                "total_iterations": len(result.iterations),
                "convergence_data": list(result.convergence_data),
                "timestamp": datetime.now().isoformat(),
            }
        )

    def _export_results(self, result: DesignResult) -> None:
        history_path = os.path.join(self.output_dir, "autonomous_history.json")
        self._append_to_json(history_path, self.history)

        decisions_path = os.path.join(self.output_dir, "autonomous_decisions.json")
        decisions_data = [d.to_dict() for d in self.decision_engine.decision_history]
        self._write_json(decisions_path, decisions_data)

        iterations_path = os.path.join(self.output_dir, "autonomous_iterations.json")
        iterations_data = [i.to_dict() for i in result.iterations]
        self._write_json(iterations_path, iterations_data)

        metrics_path = os.path.join(self.output_dir, "autonomous_metrics.json")
        metrics_data = {
            "result_id": result.result_id,
            "final_scores": result.final_scores,
            "convergence_data": result.convergence_data,
            "total_duration_seconds": result.total_duration_seconds,
            "success": result.success,
            "total_iterations": len(result.iterations),
        }
        self._write_json(metrics_path, metrics_data)

        # Visualisation
        try:
            from .autonomous_visualizer import AutonomousVisualizer  # local import

            visualizer = AutonomousVisualizer(self.output_dir)
            visualizer.plot_iteration_scores(result)
            visualizer.plot_critic_progress(result)
            visualizer.plot_optimization_curve(result)
        except Exception as exc:
            logger.debug("Visualisation step failed: %s", exc)

    def _export_benchmark(self, report: Dict[str, Any]) -> None:
        benchmark_path = os.path.join(self.output_dir, "benchmark_report.json")
        self._write_json(benchmark_path, report)

    def _write_json(self, path: str, data: Any) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)

    def _append_to_json(self, path: str, data: Any) -> None:
        existing: Any = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, OSError):
                existing = []
        if isinstance(existing, list):
            existing.extend(data if isinstance(data, list) else [data])
        else:
            existing = data
        self._write_json(path, existing)

    def _lazy_load_subsystems(self) -> None:
        """Best-effort load of the real subsystems if they were not injected."""
        if self.knowledge_engine is None:
            cls = _try_load("core.knowledge.KnowledgeEngine")
            if cls is not None:
                try:
                    self.knowledge_engine = cls()
                    self.director.knowledge_engine = self.knowledge_engine
                    self.decision_engine.knowledge_engine = self.knowledge_engine
                except Exception as exc:
                    logger.debug("KnowledgeEngine init failed: %s", exc)
        if self.blueprint_intelligence is None:
            cls = _try_load("core.blueprint_intelligence.BlueprintIntelligenceEngine")
            if cls is not None:
                try:
                    self.blueprint_intelligence = cls()
                    self.director.blueprint_intelligence = self.blueprint_intelligence
                    self.decision_engine.blueprint_intelligence = (
                        self.blueprint_intelligence
                    )
                except Exception as exc:
                    logger.debug("BlueprintIntelligence init failed: %s", exc)
        if self.visual_critic is None:
            cls = _try_load("core.critic.VisualCritic")
            if cls is not None:
                try:
                    self.visual_critic = cls()
                    self.optimizer.visual_critic = self.visual_critic
                except Exception as exc:
                    logger.debug("VisualCritic init failed: %s", exc)

    # ------------------------------------------------------------------ I/O

    def to_dict(self) -> Dict[str, Any]:
        return {
            "director": self.director.to_dict(),
            "planner": self.planner.to_dict(),
            "decision_engine": self.decision_engine.to_dict(),
            "optimizer": self.optimizer.to_dict(),
            "goal_manager": self.goal_manager.to_dict(),
            "history": self.history,
            "output_dir": self.output_dir,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutonomousWorldDesigner":
        designer = cls()
        if "director" in data:
            designer.director = AutonomousDirector.from_dict(data["director"])
        if "planner" in data:
            designer.planner = AutonomousPlanner.from_dict(data["planner"])
        if "decision_engine" in data:
            designer.decision_engine = AutonomousDecisionEngine.from_dict(
                data["decision_engine"]
            )
        if "optimizer" in data:
            designer.optimizer = AutonomousOptimizer.from_dict(data["optimizer"])
        if "goal_manager" in data:
            designer.goal_manager = GoalManager.from_dict(data["goal_manager"])
        if "history" in data:
            designer.history = data["history"]
        if "output_dir" in data:
            designer.output_dir = data["output_dir"]
        return designer
