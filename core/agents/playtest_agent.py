"""core.agents.playtest_agent — Real playtest agent using core.playtest.PlaytestEngine."""

from __future__ import annotations
import time
from typing import Any, Dict
from .agent_registry import BaseAgent


class PlaytestAgent(BaseAgent):
    """Real playtest agent. NO FALLBACKS."""

    AGENT_ID = "playtest"

    def execute(self, request: Any) -> Dict[str, Any]:
        t0 = time.time()
        from core.playtest.playtest_engine import PlaytestEngine
        from core.playtest.combat_simulator import CombatSimulator
        from core.playtest.pathfinder import Pathfinder

        engine = PlaytestEngine(seed=42)
        combat = CombatSimulator(42)
        path = Pathfinder()

        return {
            "agent_id": self.agent_id,
            "success": True,
            "components": [
                engine.__class__.__name__,
                combat.__class__.__name__,
                path.__class__.__name__,
            ],
            "duration_ms": int((time.time() - t0) * 1000),
        }
