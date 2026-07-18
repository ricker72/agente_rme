"""
Autonomous Director — decides what to build and how to build it.

The Director is the high-level reasoning component of the autonomous world
designer.  It accepts a natural-language prompt (or a programmatic
:class:`DesignGoal`) and produces a concrete set of :class:`RegionPlan`
objects that describe the world to be generated.

The Director consumes the real subsystems of the agent:

* ``KnowledgeEngine`` — to retrieve similar hunts, cities, boss rooms, …
* ``BlueprintIntelligenceEngine`` — to recommend blueprints and patterns.
* ``VisualCritic`` — to bias decisions based on previous critic outcomes.

All those integrations are optional: if a subsystem is unavailable the
Director falls back to deterministic heuristics so the pipeline still
runs end-to-end.
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .models.design_goal import DesignGoal
from .models.region_plan import RegionPlan

logger = logging.getLogger(__name__)


# ── Theme → archetype hints used by the heuristics ──────────────────────────
THEME_HINTS: Dict[str, Dict[str, str]] = {
    "issavi": {"city": "issavi_city", "hunt": "issavi_dunes", "boss": "issavi_pharaoh"},
    "roshamuul": {
        "city": "roshamuul_hub",
        "hunt": "roshamuul_citadel",
        "boss": "roshamuul_lord",
    },
    "desert": {"city": "desert_oasis", "hunt": "desert_dunes", "boss": "desert_sphinx"},
    "forest": {
        "city": "forest_grove",
        "hunt": "forest_clearing",
        "boss": "forest_treant",
    },
    "ice": {"city": "frosthold", "hunt": "frozen_tundra", "boss": "ice_dragon"},
}


@dataclass
class AutonomousDirector:
    """Decides what to build, how to build it, and which assets to use."""

    knowledge_engine: Any = None
    blueprint_intelligence: Any = None
    visual_critic: Any = None
    decision_memory: List[Dict[str, Any]] = field(default_factory=list)

    # ------------------------------------------------------------------ public

    def parse_prompt(self, prompt: str) -> DesignGoal:
        """Parse a natural language prompt into a :class:`DesignGoal`."""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        goal = DesignGoal(prompt=prompt)
        lower = prompt.lower()

        # Level range (e.g. "nivel 300-500", "level 300")
        level_range = self._extract_level_range(lower)
        if level_range is not None:
            goal.level_range = level_range

        # Hunt / boss / raid counts
        hunt_match = re.search(r"(\d+)\s*hunt", lower)
        if hunt_match:
            goal.num_hunts = int(hunt_match.group(1))
        boss_match = re.search(r"(\d+)\s*boss", lower)
        if boss_match:
            goal.num_bosses = int(boss_match.group(1))
        raid_match = re.search(r"(\d+)\s*raid", lower)
        if raid_match:
            goal.num_raids = int(raid_match.group(1))

        # Strategy
        if "city" in lower and "compact" in lower:
            goal.strategy = "city_focused"
        elif "hunt" in lower:
            goal.strategy = "hunt_focused"
        elif "boss" in lower:
            goal.strategy = "boss_focused"
        elif "raid" in lower:
            goal.strategy = "campaign_focused"
        elif "large" in lower or "continent" in lower:
            goal.strategy = "aggressive_expansion"
        else:
            goal.strategy = "balanced"

        return goal

    def decide_regions(self, goal: DesignGoal) -> List[RegionPlan]:
        """Decide which regions to create for the given goal."""
        regions: List[RegionPlan] = []

        theme = self._detect_theme(goal.prompt)

        for i in range(goal.num_hunts):
            regions.append(
                self._make_region(goal, idx=i, region_type="hunt", theme=theme)
            )
        for i in range(goal.num_bosses):
            regions.append(
                self._make_region(goal, idx=i, region_type="boss", theme=theme)
            )
        for i in range(goal.num_raids):
            regions.append(
                self._make_region(goal, idx=i, region_type="raid", theme=theme)
            )

        # Always include at least a city hub (unless strategy is purely hunt focused
        # and zero cities are explicitly requested via prompt).
        if "compact" not in goal.prompt.lower() or goal.num_hunts == 0:
            regions.append(
                self._make_region(goal, idx=0, region_type="city", theme=theme)
            )
        else:
            # Compact city-only mode: produce a single city region
            regions.append(
                self._make_region(goal, idx=0, region_type="city", theme=theme)
            )

        return regions

    def select_blueprints(self, region: RegionPlan) -> List[str]:
        """Select blueprint candidates for a region.

        Prefers the :class:`BlueprintIntelligenceEngine` when available.
        """
        bp_options: List[str] = []

        if self.blueprint_intelligence is not None:
            try:
                # Use a type-based query that the engine understands
                recs = self.blueprint_intelligence.recommend(
                    region.region_type, top_k=5
                )
                for rec in recs[:3]:
                    if isinstance(rec, dict):
                        name = rec.get("name") or rec.get("recommendation")
                        if name:
                            bp_options.append(str(name))
                    elif hasattr(rec, "name"):
                        bp_options.append(rec.name)
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("BlueprintIntelligence recommend failed: %s", exc)

        if not bp_options:
            bp_options = self._heuristic_blueprints(region)

        # Deduplicate while preserving order
        seen = set()
        unique: List[str] = []
        for bp in bp_options:
            if bp not in seen:
                seen.add(bp)
                unique.append(bp)
        return unique

    def select_patterns(self, region: RegionPlan) -> List[str]:
        """Select layout patterns for a region.

        Tries the KnowledgeEngine first, then falls back to heuristics.
        """
        patterns: List[str] = []

        if self.knowledge_engine is not None:
            try:
                finders = {
                    "hunt": self.knowledge_engine.find_similar_hunts,
                    "city": self.knowledge_engine.find_similar_cities,
                    "boss": self.knowledge_engine.find_similar_boss_rooms,
                    "raid": self.knowledge_engine.find_similar_raids,
                    "mixed": self.knowledge_engine.find_similar_regions,
                }
                finder = finders.get(
                    region.region_type, self.knowledge_engine.find_similar_regions
                )
                results = finder(region.region_name, k=3)
                for entry in results:
                    if isinstance(entry, dict):
                        name = entry.get("name") or entry.get("entry", {}).get("name")
                        if name:
                            patterns.append(str(name))
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("KnowledgeEngine lookup failed: %s", exc)

        if not patterns:
            patterns = self._heuristic_patterns(region)

        return patterns

    def record_decision(
        self,
        decision_type: str,
        region_id: str,
        selected_option: str,
        score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a decision for memory and downstream analysis."""
        self.decision_memory.append(
            {
                "decision_id": str(uuid.uuid4()),
                "decision_type": decision_type,
                "region_id": region_id,
                "selected_option": selected_option,
                "score": float(score),
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat(),
            }
        )

    def get_memory_stats(self) -> Dict[str, Any]:
        """Return aggregate statistics over the decision memory."""
        if not self.decision_memory:
            return {
                "total_decisions": 0,
                "average_score": 0.0,
                "best_score": 0.0,
                "worst_score": 0.0,
            }

        scores = [float(d["score"]) for d in self.decision_memory]
        return {
            "total_decisions": len(self.decision_memory),
            "average_score": sum(scores) / len(scores),
            "best_score": max(scores),
            "worst_score": min(scores),
        }

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _extract_level_range(text: str) -> Optional[Tuple[int, int]]:
        # "nivel 300-500", "level 300-500"
        m = re.search(r"(?:nivel|level)\s*(\d+)\s*[-–]\s*(\d+)", text)
        if m:
            lo, hi = sorted([int(m.group(1)), int(m.group(2))])
            return (lo, hi)
        # "level 300" → ± 50
        m = re.search(r"(?:nivel|level)\s*(\d+)", text)
        if m:
            lvl = int(m.group(1))
            return (max(1, lvl - 50), lvl + 50)
        return None

    @staticmethod
    def _detect_theme(prompt: str) -> str:
        lower = prompt.lower()
        for theme in THEME_HINTS:
            if theme in lower:
                return theme
        if "desert" in lower:
            return "desert"
        if "snow" in lower or "ice" in lower:
            return "ice"
        if "forest" in lower or "jungle" in lower:
            return "forest"
        return "issavi"

    @staticmethod
    def _make_region(
        goal: DesignGoal, idx: int, region_type: str, theme: str
    ) -> RegionPlan:
        defaults = {
            "hunt": {"size": 1200, "density": 0.55, "difficulty": 0.4},
            "boss": {"size": 600, "density": 0.70, "difficulty": 0.85},
            "raid": {"size": 900, "density": 0.65, "difficulty": 0.95},
            "city": {"size": 800, "density": 0.45, "difficulty": 0.10},
            "mixed": {"size": 700, "density": 0.50, "difficulty": 0.50},
        }
        d = defaults[region_type]
        hints = THEME_HINTS.get(theme, {})
        archetype = hints.get(region_type, f"{region_type}_{theme}")
        name_suffix = "" if region_type == "city" else f" {idx + 1}"
        return RegionPlan(
            region_id=f"{region_type}_{idx + 1}",
            region_name=f"{archetype.replace('_', ' ').title()}{name_suffix}",
            region_type=region_type,
            description=f"{region_type.title()} region for level {goal.level_range[0]}-{goal.level_range[1]}",
            level_range=goal.level_range,
            target_size=d["size"],
            target_density=d["density"],
            target_difficulty=d["difficulty"],
        )

    @staticmethod
    def _heuristic_blueprints(region: RegionPlan) -> List[str]:
        base = region.region_type
        return [f"blueprint_{base}_core_{i + 1}" for i in range(3)]

    @staticmethod
    def _heuristic_patterns(region: RegionPlan) -> List[str]:
        return [f"pattern_{region.region_type}_{region.region_id}"]

    # ------------------------------------------------------------------ I/O

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_memory": self.decision_memory,
            "memory_stats": self.get_memory_stats(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutonomousDirector":
        director = cls()
        if "decision_memory" in data:
            director.decision_memory = list(data["decision_memory"])
        return director
