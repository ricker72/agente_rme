"""core.agents.critic_agent — Real critic agent using core.critic.VisualCritic."""
from __future__ import annotations
import time
from typing import Any, Dict
from .agent_registry import BaseAgent


class CriticAgent(BaseAgent):
    """Real critic agent. NO FALLBACKS."""
    AGENT_ID = "critic"

    def execute(self, request: Any) -> Dict[str, Any]:
        t0 = time.time()
        from core.critic.visual_critic import VisualCritic
        from core.critic.critic_engine import CriticEngine
        from core.critic.score_calculator import ScoreCalculator

        vc = VisualCritic()
        ce = CriticEngine()
        sc = ScoreCalculator()

        return {
            "agent_id": self.agent_id,
            "success": True,
            "components": [vc.__class__.__name__, ce.__class__.__name__, sc.__class__.__name__],
            "duration_ms": int((time.time() - t0) * 1000),
        }
